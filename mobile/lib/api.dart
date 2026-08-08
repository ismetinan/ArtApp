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
  final bool unlockedByScore;

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
            .toList(),
        unlockedByScore = j['unlocked_by_score'] == true;
}

class GalleryItem {
  final int submissionId;
  final String displayName, createdAt;
  final String? nodeTitle;
  final bool isMine;

  GalleryItem.fromJson(Map<String, dynamic> j)
      : submissionId = j['submission_id'],
        displayName = j['display_name'],
        nodeTitle = j['node_title'],
        isMine = j['is_mine'] == true,
        createdAt = j['created_at'];
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

/// Faz 2: mentor kartı/profili
class MentorInfo {
  final int id, userId, answeredCount;
  final String displayName, bio;
  final List<String> styles;
  final List<int> portfolioSubmissionIds;
  final double? rating;
  final bool isAvailable;

  /// Bağış bağlantısı — yalnız mentor profili DETAYINDA ve yalnız admin
  /// onayından geçmişse sunucudan gelir (listede hiç gelmez). Ödeme uygulama
  /// dışında, %100 mentora; Artora kesinti almaz ve akışa girmez.
  final String? donationUrl, donationPlatform;

  MentorInfo.fromJson(Map<String, dynamic> j)
      : id = j['id'],
        userId = j['user_id'],
        displayName = j['display_name'],
        bio = j['bio'],
        styles = List<String>.from(j['styles'] ?? []),
        portfolioSubmissionIds = List<int>.from(j['portfolio_submission_ids'] ?? []),
        rating = (j['rating'] as num?)?.toDouble(),
        answeredCount = j['answered_count'] ?? 0,
        isAvailable = j['is_available'] ?? true,
        donationUrl = j['donation_url'],
        donationPlatform = j['donation_platform'];
}

/// Faz 2: öğrencinin mentor isteği
class MentorRequestInfo {
  final int id, submissionId;
  final String? nodeId, mentorDisplayName;
  final String status, feedbackText;
  final int? rating;

  MentorRequestInfo.fromJson(Map<String, dynamic> j)
      : id = j['id'],
        submissionId = j['submission_id'],
        nodeId = j['node_id'],
        mentorDisplayName = j['mentor_display_name'],
        status = j['status'],
        feedbackText = j['feedback_text'] ?? '',
        rating = j['rating'];
}

/// Faz 2: mentor kuyruğundaki istek (öğrenci bağlamıyla)
class MentorQueueItem {
  final int id, submissionId;
  final String? nodeId;
  final String status, studentDisplayName;
  final RedlineResult? aiResult;
  // Gelir-destekli (altın) istek → öncelikli + 'derin redline' beklenir.
  // Eski backend bu alanı döndürmezse false (uyumlu).
  final bool gold;

  MentorQueueItem.fromJson(Map<String, dynamic> j)
      : id = j['id'],
        submissionId = j['submission_id'],
        nodeId = j['node_id'],
        status = j['status'],
        gold = j['gold'] == true,
        studentDisplayName = j['student_display_name'] ?? '',
        aiResult = j['ai_result'] == null
            ? null
            : RedlineResult.fromJson(Map<String, dynamic>.from(j['ai_result']));
}

/// Faz 4 (gelir paylaşımı): mentorun birikmiş kazancı (jeton-eşdeğeri).
/// Para çevrimi + ödeme altyapısı Faz B — şimdilik salt biriktirme/gösterim.
/// Mentorun defter özeti. Yeni ekonomide PARA değil İTİBAR: mentorluk ücretsiz,
/// mentora ödeme yalnız uygulama dışı bağışla ve Artora akışa girmiyor.
/// jetonEquivalent eski ekonomi kayıtları için korunuyor.
class EarningsInfo {
  final int jetonEquivalent, answeredCount;
  final double? rating;

  EarningsInfo.fromJson(Map<String, dynamic> j)
      : jetonEquivalent = j['jeton_equivalent'] ?? 0,
        answeredCount = j['answered_count'] ?? 0,
        rating = (j['rating'] as num?)?.toDouble();
}

/// Asenkron analiz işinin durumu (Faz 2).
class AnalysisJobInfo {
  final int jobId;
  final String status; // queued | running | done | failed
  final String kind; // assignment | free
  final String? nodeId;
  final int? submissionId;
  final RedlineResult? analysis;
  final int xpAwarded;

  /// Sunucudan YERELLEŞTİRİLMİŞ gelir; istemci hata anahtarı sözlüğü tutmaz.
  final String? error;

  bool get isFinished => status == 'done' || status == 'failed';

  AnalysisJobInfo.fromJson(Map<String, dynamic> j)
      : jobId = j['job_id'],
        status = j['status'],
        kind = j['kind'] ?? 'assignment',
        nodeId = j['node_id'],
        submissionId = j['submission_id'],
        analysis =
            j['analysis'] == null ? null : RedlineResult.fromJson(j['analysis']),
        xpAwarded = j['xp_awarded'] ?? 0,
        error = j['error'];
}

class ApiClient {
  ApiClient._();
  static final instance = ApiClient._();

  String? token;
  bool isGuest = true;

  /// Backend'deki mentor_market_enabled flag'i — mentor UI'ı buna göre görünür.
  bool mentorMarketEnabled = false;

  /// Backend'deki billing_enabled flag'i (sunucu tarafı, platformdan bağımsız).
  bool _billingEnabledServer = false;

  /// Backend'deki jeton_ai_economy_enabled flag'i. Açıkken jeton = AI kullanım
  /// birimi ve mentorluk ücretsiz; kapalıyken jeton = mentor parası (eski model).
  /// Metinler ve bedel uyarıları buna göre seçilir.
  bool jetonAiEconomy = false;

  /// Haftalık ücretsiz jeton tabanı ("her hafta 3'e tamamlanır" bilgisi).
  int weeklyJetonFloor = 3;

  /// AI aksiyon fiyatları (redline / serbest analiz) — sunucudan gelir.
  int aiCostRedline = 1;
  int aiCostFreeAnalysis = 1;

  /// Mağaza UI'ı buna göre görünür. iOS'ta satın alma henüz yok — App Store
  /// Connect'te ürün tanımlı değil — bu yüzden sunucu açık dese de kapalı
  /// sayılır; aksi halde boş bir mağaza ve çalışmayan "Jeton Al" akışı çıkardı.
  bool get billingEnabled => !Platform.isIOS && _billingEnabledServer;

  /// Kullanıcı seviye belirleme ekranını bilerek atladı (cihaz-yerel tercih).
  /// Atlamadıysa ve chart boşsa açılışta 3-resim ekranına geri yönlendirilir.
  bool onboardingSkipped = false;

  /// Kullanıcının açıkça seçtiği dil (profildeki seçici). null = cihaz dili.
  String? savedLanguage;

  /// Profildeki karanlık tema anahtarı — yalnız cihaz-yerel tercih (backend'e yazılmaz).
  bool darkMode = false;

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
    darkMode = prefs.getBool('dark_mode') ?? false;
    mentorMarketEnabled = prefs.getBool('mentor_market') ?? false;
    _billingEnabledServer = prefs.getBool('billing') ?? false;
    onboardingSkipped = prefs.getBool('onboarding_skipped') ?? false;
  }

  Future<void> setOnboardingSkipped() async {
    onboardingSkipped = true;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('onboarding_skipped', true);
  }

  /// FCM cihaz token'ını backend'e kaydeder (push bildirimleri için).
  Future<void> registerDevice(String fcmToken) async {
    final r = await http.put(
      Uri.parse('$apiBase/users/me/device'),
      headers: _jsonHeaders,
      body: jsonEncode({'fcm_token': fcmToken}),
    );
    _decode(r);
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

  /// Karanlık tema anahtarı: yerelde saklar, sunucuya yazılmaz (salt UI tercihi).
  Future<void> setDarkMode(bool value) async {
    darkMode = value;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('dark_mode', value);
  }

  Future<void> _saveSession(Map<String, dynamic> auth) async {
    token = auth['token'];
    isGuest = auth['is_guest'];
    mentorMarketEnabled = auth['mentor_market_enabled'] ?? false;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('token', token!);
    await prefs.setBool('is_guest', isGuest);
    await prefs.setBool('mentor_market', mentorMarketEnabled);
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

  /// Oturumu kapatır (hesap sunucuda kalır). Önce bu cihazın FCM token'ını
  /// hesaptan ayırmayı dener ki eski hesabın bildirimleri bu telefona düşmesin;
  /// başarısız olsa da çıkış devam eder.
  Future<void> logout() async {
    try {
      await registerDevice('');
    } catch (_) {}
    await clearSession();
  }

  Future<void> clearSession() async {
    token = null;
    isGuest = true;
    onboardingSkipped = false;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('token');
    await prefs.remove('is_guest');
    await prefs.remove('onboarding_skipped');
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

  Future<({List<SkillNode> nodes, String? recommendedNodeId})> getTree() async {
    final r = await http.get(Uri.parse('$apiBase/skill-tree'), headers: authHeaders);
    final j = _decode(r);
    return (
      nodes: (j['nodes'] as List).map((n) => SkillNode.fromJson(n)).toList(),
      recommendedNodeId: j['recommended_node_id'] as String?,
    );
  }

  /// Kayıtlı AI ödevini getirir (yoksa null; kota harcamaz).
  Future<String?> getAssignment(String nodeId) async {
    final r = await http.get(
        Uri.parse('$apiBase/skill-tree/$nodeId/assignment'), headers: authHeaders);
    return _decode(r)['assignment'] as String?;
  }

  /// AI'a kişisel ödev görevi ürettirir (düğüm başına bir kez kota harcar).
  Future<String> generateAssignment(String nodeId) async {
    final r = await http.post(
        Uri.parse('$apiBase/skill-tree/$nodeId/assignment'), headers: authHeaders);
    return _decode(r)['assignment'] as String;
  }

  /// Serbest çizim analizi (ders dışı; ücretsizde haftada 1, 429 döner).
  Future<({RedlineResult analysis, int xpAwarded, int level, int submissionId})>
      submitFreeAnalysis(List<int> bytes, String name) async {
    final req = http.MultipartRequest('POST', Uri.parse('$apiBase/free-analysis'))
      ..headers.addAll(authHeaders)
      ..files.add(http.MultipartFile.fromBytes('file', bytes, filename: name));
    final r = await http.Response.fromStream(await req.send());
    final j = _decode(r);
    return (
      analysis: RedlineResult.fromJson(j['analysis']),
      xpAwarded: j['xp_awarded'] as int,
      level: j['level'] as int,
      submissionId: j['submission_id'] as int,
    );
  }

  Future<({RedlineResult analysis, int xpAwarded, int level, int submissionId})>
      submitAssignment(String nodeId, List<int> bytes, String name) async {
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
      submissionId: j['submission_id'] as int,
    );
  }

  // ---------- Asenkron analiz (Faz 2) ----------
  //
  // Yükleme artık AI'ı beklemiyor: sunucu iş kimliğini hemen döner, analiz
  // arka planda koşar. Uygulama kapansa bile iş kaybolmaz — açılışta
  // getLatestAnalysisJob ile sonuç bulunur.

  Future<int> submitAssignmentAsync(
      String nodeId, List<int> bytes, String name) async {
    final req = http.MultipartRequest(
        'POST', Uri.parse('$apiBase/skill-tree/$nodeId/submit-async'))
      ..headers.addAll(authHeaders)
      ..files.add(http.MultipartFile.fromBytes('file', bytes, filename: name));
    final r = await http.Response.fromStream(await req.send());
    return _decode(r)['job_id'] as int;
  }

  Future<int> submitFreeAnalysisAsync(List<int> bytes, String name) async {
    final req =
        http.MultipartRequest('POST', Uri.parse('$apiBase/free-analysis-async'))
          ..headers.addAll(authHeaders)
          ..files.add(http.MultipartFile.fromBytes('file', bytes, filename: name));
    final r = await http.Response.fromStream(await req.send());
    return _decode(r)['job_id'] as int;
  }

  Future<AnalysisJobInfo> getAnalysisJob(int jobId) async {
    final r = await http.get(Uri.parse('$apiBase/analysis-jobs/$jobId'),
        headers: authHeaders);
    return AnalysisJobInfo.fromJson(Map<String, dynamic>.from(_decode(r)));
  }

  /// Kurtarma: son iş (varsa). Uygulama analiz sırasında kapandıysa sonuç burada.
  Future<AnalysisJobInfo?> getLatestAnalysisJob() async {
    final r = await http.get(Uri.parse('$apiBase/analysis-jobs/latest'),
        headers: authHeaders);
    final j = _decode(r)['job'];
    if (j == null) return null;
    return AnalysisJobInfo.fromJson(Map<String, dynamic>.from(j));
  }

  /// Topluluk galerisi: herkese açık paylaşılan çizimler (en yeni önce).
  Future<List<GalleryItem>> getGallery({int offset = 0, int limit = 30}) async {
    final uri = Uri.parse('$apiBase/gallery')
        .replace(queryParameters: {'offset': '$offset', 'limit': '$limit'});
    final r = await http.get(uri, headers: authHeaders);
    return (_decode(r)['items'] as List)
        .map((m) => GalleryItem.fromJson(Map<String, dynamic>.from(m)))
        .toList();
  }

  /// Topluluk gönderisini şikayet eder (UGC moderasyonu).
  Future<void> reportSubmission(int submissionId, String reason) async {
    final r = await http.post(
      Uri.parse('$apiBase/submissions/$submissionId/report'),
      headers: _jsonHeaders,
      body: jsonEncode({'reason': reason}),
    );
    _decode(r);
  }

  /// Admin: bekleyen içerik şikayetleri.
  Future<List<Map<String, dynamic>>> getContentReports() async {
    final r =
        await http.get(Uri.parse('$apiBase/admin/reports'), headers: authHeaders);
    return (_decode(r)['reports'] as List)
        .map((m) => Map<String, dynamic>.from(m))
        .toList();
  }

  /// Admin: şikayet kararı — hide (kaldır) | dismiss (içerik kalır).
  Future<void> decideContentReport(int submissionId, bool hide) async {
    final decision = hide ? 'hide' : 'dismiss';
    final r = await http.post(
      Uri.parse('$apiBase/admin/reports/$submissionId/$decision'),
      headers: authHeaders,
    );
    _decode(r);
  }

  Future<Map<String, dynamic>> getProfile() async {
    final r = await http.get(Uri.parse('$apiBase/profile'), headers: authHeaders);
    final j = _decode(r);
    mentorMarketEnabled = j['mentor_market_enabled'] ?? mentorMarketEnabled;
    jetonAiEconomy = j['jeton_ai_economy'] ?? jetonAiEconomy;
    weeklyJetonFloor = j['weekly_jeton_floor'] ?? weeklyJetonFloor;
    final costs = j['ai_costs'];
    if (costs is Map) {
      aiCostRedline = costs['redline'] ?? aiCostRedline;
      aiCostFreeAnalysis = costs['free_analysis'] ?? aiCostFreeAnalysis;
    }
    final billing = j['billing_enabled'];
    if (billing is bool && billing != _billingEnabledServer) {
      _billingEnabledServer = billing;
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool('billing', billing);
    }
    return j;
  }

  // ---------- Play Billing ----------

  /// Satın almayı backend'e doğrulatır; hak sunucuda verilir.
  /// 200 dönmeden completePurchase ÇAĞRILMAMALI.
  Future<Map<String, dynamic>> verifyPurchase(
      String productId, String purchaseToken) async {
    final r = await http.post(
      Uri.parse('$apiBase/billing/verify'),
      headers: _jsonHeaders,
      body: jsonEncode({
        'product_id': productId,
        'purchase_token': purchaseToken,
      }),
    );
    return _decode(r);
  }

  /// Açılışta abonelik durumunu tazeler (lazy yenileme).
  Future<Map<String, dynamic>> getBillingStatus() async {
    final r =
        await http.get(Uri.parse('$apiBase/billing/status'), headers: authHeaders);
    return _decode(r);
  }

  // ---------- Faz 2: mentor pazarı ----------

  Future<List<MentorInfo>> getMentors({String? style, String? query}) async {
    final params = <String, String>{
      'style': ?style,
      if (query != null && query.isNotEmpty) 'q': query,
    };
    final uri = Uri.parse('$apiBase/mentors')
        .replace(queryParameters: params.isEmpty ? null : params);
    final r = await http.get(uri, headers: authHeaders);
    return (_decode(r)['mentors'] as List)
        .map((m) => MentorInfo.fromJson(Map<String, dynamic>.from(m)))
        .toList();
  }

  /// Tek mentorun detayı. Liste yanıtından farkı: onaylı bağış bağlantısı
  /// yalnız burada döner (listede bilinçli yok).
  Future<MentorInfo> getMentor(int profileId) async {
    final r =
        await http.get(Uri.parse('$apiBase/mentors/$profileId'), headers: authHeaders);
    return MentorInfo.fromJson(Map<String, dynamic>.from(_decode(r)));
  }

  /// Ödevi mentora gönderir: mentorProfileId verilirse seçmeli (3 jeton),
  /// verilmezse havuzdan rastgele (1 jeton).
  Future<({String mentorName, int jetonBalance})> requestMentor(
      int submissionId, {int? mentorProfileId}) async {
    final r = await http.post(
      Uri.parse('$apiBase/submissions/$submissionId/mentor-request'),
      headers: _jsonHeaders,
      body: mentorProfileId == null
          ? null
          : jsonEncode({'mentor_id': mentorProfileId}),
    );
    final j = _decode(r);
    return (
      mentorName: j['mentor_display_name'] as String,
      jetonBalance: j['jeton_balance'] as int,
    );
  }

  Future<List<MentorRequestInfo>> getMyMentorRequests() async {
    final r =
        await http.get(Uri.parse('$apiBase/mentor-requests'), headers: authHeaders);
    return (_decode(r)['requests'] as List)
        .map((m) => MentorRequestInfo.fromJson(Map<String, dynamic>.from(m)))
        .toList();
  }

  Future<void> rateMentorRequest(int requestId, int rating) async {
    final r = await http.post(
      Uri.parse('$apiBase/mentor-requests/$requestId/rating'),
      headers: _jsonHeaders,
      body: jsonEncode({'rating': rating}),
    );
    _decode(r);
  }

  Future<void> applyMentor(
    String bio,
    List<String> styles,
    List<int> portfolioIds, {
    String sampleCritique = '',
    bool rulesAccepted = false,
    String? donationUrl,
  }) async {
    final r = await http.post(
      Uri.parse('$apiBase/mentors/apply'),
      headers: _jsonHeaders,
      body: jsonEncode({
        'bio': bio,
        'styles': styles,
        'portfolio_submission_ids': portfolioIds,
        'sample_critique': sampleCritique,
        'rules_accepted': rulesAccepted,
        'donation_url': donationUrl,
      }),
    );
    _decode(r);
  }

  /// Mentorun kendi profili — bağış linki durumu dahil (onaysızken de görür).
  Future<Map<String, dynamic>> getMentorMe() async {
    final r = await http.get(Uri.parse('$apiBase/mentor/me'), headers: authHeaders);
    return Map<String, dynamic>.from(_decode(r));
  }

  /// Admin: bağış bağlantısını onaylar/reddeder (başvuru onayından ayrı).
  Future<void> decideDonationLink(int profileId, bool approve) async {
    final decision = approve ? 'approve' : 'reject';
    final r = await http.post(
      Uri.parse('$apiBase/admin/mentor-profiles/$profileId/donation/$decision'),
      headers: authHeaders,
    );
    _decode(r);
  }

  Future<void> setMentorAvailability(bool isAvailable) async {
    final r = await http.patch(
      Uri.parse('$apiBase/mentor/me'),
      headers: _jsonHeaders,
      body: jsonEncode({'is_available': isAvailable}),
    );
    _decode(r);
  }

  Future<List<MentorQueueItem>> getMentorQueue() async {
    final r = await http.get(Uri.parse('$apiBase/mentor/queue'), headers: authHeaders);
    return (_decode(r)['requests'] as List)
        .map((m) => MentorQueueItem.fromJson(Map<String, dynamic>.from(m)))
        .toList();
  }

  /// Mentorun defter özeti (cevaplanan istek + puan). Yalnız onaylı mentor.
  Future<EarningsInfo> getMentorStats() async {
    final r = await http.get(Uri.parse('$apiBase/mentor/stats'), headers: authHeaders);
    return EarningsInfo.fromJson(Map<String, dynamic>.from(_decode(r)));
  }

  Future<void> sendMentorFeedback(int requestId, String text) async {
    final r = await http.post(
      Uri.parse('$apiBase/mentor-requests/$requestId/feedback'),
      headers: _jsonHeaders,
      body: jsonEncode({'feedback_text': text}),
    );
    _decode(r);
  }

  /// Admin: bekleyen mentor başvuruları (is_admin olmayan hesapta 403 alır).
  Future<List<Map<String, dynamic>>> getMentorApplications() async {
    final r = await http.get(
      Uri.parse('$apiBase/admin/mentor-applications'),
      headers: authHeaders,
    );
    return (_decode(r)['applications'] as List)
        .map((m) => Map<String, dynamic>.from(m))
        .toList();
  }

  /// Admin: başvuruyu onaylar/reddeder.
  Future<void> decideMentorApplication(int profileId, bool approve) async {
    final decision = approve ? 'approve' : 'reject';
    final r = await http.post(
      Uri.parse('$apiBase/admin/mentor-applications/$profileId/$decision'),
      headers: authHeaders,
    );
    _decode(r);
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

/// Mentor stil anahtarlarının görünen halleri (backend anahtar saklar).
Map<String, String> styleLabels(AppLocalizations t) => {
      'manga': t.styleManga,
      'realist': t.styleRealist,
      'karikatur': t.styleKarikatur,
      'anime': t.styleAnime,
      'dijital': t.styleDijital,
      'karakalem': t.styleKarakalem,
    };

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
