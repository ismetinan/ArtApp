import 'dart:convert';

import 'package:artapp/api.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Hata: hesap Türkçe açılmış, telefon/uygulama sonradan İngilizce → arayüz
/// İngilizce ama AI geri bildirimi Türkçe geliyordu.
void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({});
    ApiClient.instance.token = 't';
  });

  Future<List<http.Request>> run(String appLang, String serverLang) async {
    final calls = <http.Request>[];
    ApiClient.instance.savedLanguage = appLang;
    final client = MockClient((req) async {
      calls.add(req);
      if (req.url.path == '/profile') {
        return http.Response.bytes(
            utf8.encode(jsonEncode({'language': serverLang, 'level': 1})), 200);
      }
      return http.Response('{}', 200);
    });
    await http.runWithClient(() async {
      final p = await ApiClient.instance.getProfile();
      expect(p['language'], appLang);
      await Future<void>.delayed(Duration.zero);
    }, () => client);
    return calls;
  }

  test('sunucu dili farklıysa uygulamanın diline eşitlenir', () async {
    final calls = await run('en', 'tr');
    final patch = calls.where((c) => c.method == 'PATCH').single;
    expect(patch.url.path, '/users/me/language');
    expect(jsonDecode(patch.body), {'language': 'en'});
  });

  test('aynıysa istek gönderilmez', () async {
    final calls = await run('tr', 'tr');
    expect(calls.where((c) => c.method == 'PATCH'), isEmpty);
  });
}
