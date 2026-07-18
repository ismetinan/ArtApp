import 'dart:convert';
import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/widgets.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import 'l10n/gen/app_localizations.dart';

/// Backend adresi. Telefonda: `flutter run --dart-define=API_BASE=http://BILGISAYAR-LAN-IP:8000`
const apiBase = String.fromEnvironment('API_BASE', defaultValue: 'http://localhost:8000');

/// Backend'den dönen hata (detail mesajıyla). SocketException = sunucuya ulaşılamadı.
/// detail zaten kullanıcının dilinde gelir (backend mesaj kataloğu).
class ApiException implements Exception {
  final int statusCode;
  final String message;
  ApiException(this.statusCode, this.message);

  @override
  String toString() => message;
}

/// Kullanıcıya gösterilecek hata metni üretir (seçili UI dilinde).
String friendlyError(BuildContext context, Object e) {
  final t = AppLocalizations.of(context);
  if (e is SocketException || (e is http.ClientException)) {
    return t.errorNetwork;
  }
  if (e is ApiException) return e.message;
  return t.errorUnexpected;
}

Map<String, dynamic> _decode(http.Response r) {
  final body = jsonDecode(utf8.decode(r.bodyBytes));
  if (r.statusCode >= 400) {
    // detail yoksa dil-bağımsız kısa bir kod göster
    throw ApiException(
        r.statusCode, (body is Map ? body['detail'] : null) ?? 'HTTP ${r.statusCode}');
  }
  return body as Map<String, dynamic>;
}

/// Bir dersin video/playlist kaynağı (müfredat: art_sources.md).
class NodeResource {
  final String kind, youtubeId, title, author;

  NodeResource.fromJson(Map<String, dynamic> j)
      : kind = j['kind'],
        youtubeId = j['youtube_id'],
        title = j['title'],
        author = j['author'];

  bool get isPlaylist => kind == 'playlist';

  Uri get url => Uri.parse(isPlaylist
      ? 'https://www.youtube.com/playlist?list=$youtubeId'
      : 'https://youtu.be/$youtubeId');
}

class SkillNode {
  final String id, title, description, youtubeVideoId, skillAxis, status;
  final int xpReward;
  final List<String> prerequisites;
  final List<NodeResource> resources;

  SkillNode.fromJson(Map<String, dynamic> j)
      : id = j['id'],
        title = j['title'],
        description = j['description'],
        youtubeVideoId = j['youtube_video_id'],
        skillAxis = j['skill_axis'],
        status = j['status'],
        xpReward = j['xp_reward'],
        prerequisites = List<String>.from(j['prerequisites']),
        resources = ((j['resources'] ?? []) as List)
            .map((r) => NodeResource.fromJson(Map<String, dynamic>.from(r)))
            .toList();
}

class RedlineFinding {
  final String skillAxis, severity, messageTr, suggestionTr;
  final double x, y;

  RedlineFinding.fromJson(Map<String, dynamic> j)
      : skillAxis = j['skill_axis'],
        severity = j['severity'],
        messageTr = j['message_tr'],
        suggestionTr = j['suggestion_tr'],
        x = (j['x'] as num).toDouble(),
        y = (j['y'] as num).toDouble();
}

class RedlineResult {
  final List<String> strengthsTr;
  final List<RedlineFinding> findings;
  final String overallCommentTr;

  RedlineResult.fromJson(Map<String, dynamic> j)
      : strengthsTr = List<String>.from(j['strengths_tr']),
        findings =
            (j['findings'] as List).map((f) => RedlineFinding.fromJson(f)).toList(),
        overallCommentTr = j['overall_comment_tr'];
}

class Assessment {
  final int level;
  final Map<String, int> abilityScores;
  final String summaryTr;
  final List<String> focusAxes;

  Assessment.fromJson(Map<String, dynamic> j)
      : level = j['level'],
        abilityScores = Map<String, int>.from(j['ability_scores']),
        summaryTr = j['summary_tr'],
        focusAxes = List<String>.from(j['focus_axes']);
}

class ApiClient {
  ApiClient._();
  static final instance = ApiClient._();

  String? token;
  bool isGuest = true;

  /// Kullanıcının açıkça seçtiği dil (profildeki seçici). null = cihaz dili.
  String? savedLanguage;

  /// Backend'e gönderilen etkin dil: açık seçim > cihaz dili (tr dışı = en).
  String get language {
    if (savedLanguage != null) return savedLanguage!;
    return ui.PlatformDispatcher.instance.locale.languageCode == 'tr' ? 'tr' : 'en';
  }

  Map<String, String> get authHeaders =>
      {'Authorization': 'Bearer $token', 'Accept-Language': language};
  Map<String, String> get _jsonHeaders =>
      {...authHeaders, 'Content-Type': 'application/json'};

  String imageUrl(int submissionId) => '$apiBase/submissions/$submissionId/image';

  Future<void> loadSession() async {
    final prefs = await SharedPreferences.getInstance();
    token = prefs.getString('token');
    isGuest = prefs.getBool('is_guest') ?? true;
    savedLanguage = prefs.getString('language');
  }

  /// Dil seçici: yerelde saklar, oturum varsa backend'e de yazar
  /// (AI çıktıları ve hata mesajları da bu dile döner).
  Future<void> setLanguage(String code) async {
    savedLanguage = code;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('language', code);
    if (token != null) {
      final r = await http.patch(
        Uri.parse('$apiBase/users/me/language'),
        headers: _jsonHeaders,
        body: jsonEncode({'language': code}),
      );
      _decode(r);
    }
  }

  Future<void> _saveSession(Map<String, dynamic> auth) async {
    token = auth['token'];
    isGuest = auth['is_guest'];
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('token', token!);
    await prefs.setBool('is_guest', isGuest);
  }

  Future<void> createGuest(String displayName) async {
    final r = await http.post(
      Uri.parse('$apiBase/users/guest'),
      headers: {'Content-Type': 'application/json', 'Accept-Language': language},
      body: jsonEncode({'display_name': displayName, 'language': language}),
    );
    await _saveSession(_decode(r));
  }

  Future<void> register(String email, String password, String displayName) async {
    final r = await http.post(
      Uri.parse('$apiBase/users/register'),
      headers: {'Content-Type': 'application/json', 'Accept-Language': language},
      body: jsonEncode({
        'email': email,
        'password': password,
        'display_name': displayName,
        'language': language,
      }),
    );
    await _saveSession(_decode(r));
  }

  Future<void> login(String email, String password) async {
    final r = await http.post(
      Uri.parse('$apiBase/users/login'),
      headers: {'Content-Type': 'application/json', 'Accept-Language': language},
      body: jsonEncode({'email': email, 'password': password}),
    );
    await _saveSession(_decode(r));
  }

  Future<void> upgradeGuest(String email, String password) async {
    final r = await http.post(
      Uri.parse('$apiBase/users/upgrade'),
      headers: _jsonHeaders,
      body: jsonEncode({'email': email, 'password': password}),
    );
    await _saveSession(_decode(r));
  }

  /// Google ID token ile giriş/kayıt. Misafir oturumu açıksa token'ı da
  /// gönderir — backend misafiri ilerlemesiyle birlikte yükseltir.
  Future<void> googleLogin(String idToken) async {
    final r = await http.post(
      Uri.parse('$apiBase/users/google'),
      headers: {
        'Content-Type': 'application/json',
        'Accept-Language': language,
        if (token != null) ...authHeaders,
      },
      body: jsonEncode({'id_token': idToken, 'language': language}),
    );
    await _saveSession(_decode(r));
  }

  /// Hesabı ve tüm verileri kalıcı siler; yerel oturumu temizler.
  Future<void> deleteAccount() async {
    final r = await http.delete(Uri.parse('$apiBase/users/me'), headers: authHeaders);
    _decode(r);
    await clearSession();
  }

  Future<void> clearSession() async {
    token = null;
    isGuest = true;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('token');
    await prefs.remove('is_guest');
  }

  Future<Assessment> assessLevel(List<({List<int> bytes, String name})> images) async {
    final req = http.MultipartRequest('POST', Uri.parse('$apiBase/onboarding/assess'))
      ..headers.addAll(authHeaders);
    for (final img in images) {
      req.files.add(http.MultipartFile.fromBytes('files', img.bytes, filename: img.name));
    }
    final r = await http.Response.fromStream(await req.send());
    return Assessment.fromJson(_decode(r));
  }

  Future<List<SkillNode>> getTree() async {
    final r = await http.get(Uri.parse('$apiBase/skill-tree'), headers: authHeaders);
    return (_decode(r)['nodes'] as List).map((n) => SkillNode.fromJson(n)).toList();
  }

  Future<({RedlineResult analysis, int xpAwarded, int level})> submitAssignment(
      String nodeId, List<int> bytes, String name) async {
    final req =
        http.MultipartRequest('POST', Uri.parse('$apiBase/skill-tree/$nodeId/submit'))
          ..headers.addAll(authHeaders)
          ..files.add(http.MultipartFile.fromBytes('file', bytes, filename: name));
    final r = await http.Response.fromStream(await req.send());
    final j = _decode(r);
    return (
      analysis: RedlineResult.fromJson(j['analysis']),
      xpAwarded: j['xp_awarded'] as int,
      level: j['level'] as int,
    );
  }

  Future<Map<String, dynamic>> getProfile() async {
    final r = await http.get(Uri.parse('$apiBase/profile'), headers: authHeaders);
    return _decode(r);
  }

  Future<void> setPrivacy(int submissionId, bool isPublic) async {
    final r = await http.patch(
      Uri.parse('$apiBase/submissions/$submissionId/privacy'),
      headers: _jsonHeaders,
      body: jsonEncode({'is_public': isPublic}),
    );
    _decode(r);
  }
}

/// Eksen adlarının kullanıcıya görünen halleri (seçili UI dilinde).
/// Sıra sabit — radar chart eksen dizilimi buna dayanır.
Map<String, String> axisLabels(AppLocalizations t) => {
      'anatomi': t.axisAnatomi,
      'perspektif': t.axisPerspektif,
      'isik_golge': t.axisIsikGolge,
      'oran': t.axisOran,
      'cizgi_kalitesi': t.axisCizgiKalitesi,
      'kompozisyon': t.axisKompozisyon,
      'renk': t.axisRenk,
    };
