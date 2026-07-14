import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

/// Backend adresi. Android emülatöründe:
/// flutter run --dart-define=API_BASE=http://10.0.2.2:8000
const apiBase = String.fromEnvironment('API_BASE', defaultValue: 'http://localhost:8000');

class SkillNode {
  final String id, title, description, youtubeVideoId, skillAxis, status;
  final int xpReward;
  final List<String> prerequisites;

  SkillNode.fromJson(Map<String, dynamic> j)
      : id = j['id'],
        title = j['title'],
        description = j['description'],
        youtubeVideoId = j['youtube_video_id'],
        skillAxis = j['skill_axis'],
        status = j['status'],
        xpReward = j['xp_reward'],
        prerequisites = List<String>.from(j['prerequisites']);
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

  int? userId;

  Future<void> loadSession() async {
    userId = (await SharedPreferences.getInstance()).getInt('user_id');
  }

  Future<void> _saveSession(int id) async {
    userId = id;
    await (await SharedPreferences.getInstance()).setInt('user_id', id);
  }

  Map<String, String> get _headers => {'X-User-Id': '$userId'};

  Future<void> createGuest(String displayName) async {
    final r = await http.post(
      Uri.parse('$apiBase/users/guest'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'display_name': displayName}),
    );
    await _saveSession(jsonDecode(utf8.decode(r.bodyBytes))['id']);
  }

  Future<Assessment> assessLevel(List<({List<int> bytes, String name})> images) async {
    final req = http.MultipartRequest('POST', Uri.parse('$apiBase/onboarding/assess'))
      ..headers.addAll(_headers);
    for (final img in images) {
      req.files.add(http.MultipartFile.fromBytes('files', img.bytes, filename: img.name));
    }
    final r = await http.Response.fromStream(await req.send());
    return Assessment.fromJson(jsonDecode(utf8.decode(r.bodyBytes)));
  }

  Future<List<SkillNode>> getTree() async {
    final r = await http.get(Uri.parse('$apiBase/skill-tree'), headers: _headers);
    return (jsonDecode(utf8.decode(r.bodyBytes))['nodes'] as List)
        .map((n) => SkillNode.fromJson(n))
        .toList();
  }

  Future<({RedlineResult analysis, int xpAwarded, int level})> submitAssignment(
      String nodeId, List<int> bytes, String name) async {
    final req =
        http.MultipartRequest('POST', Uri.parse('$apiBase/skill-tree/$nodeId/submit'))
          ..headers.addAll(_headers)
          ..files.add(http.MultipartFile.fromBytes('file', bytes, filename: name));
    final r = await http.Response.fromStream(await req.send());
    final j = jsonDecode(utf8.decode(r.bodyBytes));
    return (
      analysis: RedlineResult.fromJson(j['analysis']),
      xpAwarded: j['xp_awarded'] as int,
      level: j['level'] as int,
    );
  }

  Future<Map<String, dynamic>> getProfile() async {
    final r = await http.get(Uri.parse('$apiBase/profile'), headers: _headers);
    return jsonDecode(utf8.decode(r.bodyBytes));
  }

  Future<void> setPrivacy(int submissionId, bool isPublic) async {
    await http.patch(
      Uri.parse('$apiBase/submissions/$submissionId/privacy'),
      headers: {..._headers, 'Content-Type': 'application/json'},
      body: jsonEncode({'is_public': isPublic}),
    );
  }
}

/// Eksen adlarının kullanıcıya görünen halleri
const axisLabels = {
  'anatomi': 'Anatomi',
  'perspektif': 'Perspektif',
  'isik_golge': 'Işık-Gölge',
  'oran': 'Oran',
  'cizgi_kalitesi': 'Çizgi Kalitesi',
  'kompozisyon': 'Kompozisyon',
};
