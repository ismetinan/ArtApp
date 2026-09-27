import 'dart:convert';

import 'package:artapp/api.dart';
import 'package:artapp/l10n/gen/app_localizations.dart';
import 'package:artapp/screens/gallery.dart';
import 'package:artapp/screens/info_hint.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';

Widget _wrap(Widget child) => MaterialApp(
      locale: const Locale('tr'),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: const [Locale('en'), Locale('tr')],
      home: Scaffold(body: child),
    );

final _emptyGallery = MockClient((_) async => http.Response.bytes(
    utf8.encode(jsonEncode({'items': []})), 200,
    headers: {'content-type': 'application/json'}));

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  testWidgets('Kapatılabilir ipucu ✕ ile kapanır ve bir daha görünmez', (tester) async {
    const hint = InfoHint(icon: Icons.info, text: 'Merhaba', prefsKey: 'hint_x');
    await tester.pumpWidget(_wrap(const Column(children: [hint])));
    await tester.pumpAndSettle();
    expect(find.text('Merhaba'), findsOneWidget);
    await tester.tap(find.byIcon(Icons.close));
    await tester.pumpAndSettle();
    expect(find.text('Merhaba'), findsNothing);
    expect((await SharedPreferences.getInstance()).getBool('hint_x'), isTrue);

    await tester.pumpWidget(const SizedBox());
    await tester.pumpWidget(_wrap(const Column(children: [hint])));
    await tester.pumpAndSettle();
    expect(find.text('Merhaba'), findsNothing);
  });

  testWidgets('Topluluk: seviye eşiğin altında kilit notu, üstünde paylaşım notu',
      (tester) async {
    final api = ApiClient.instance;
    api.token = 't';
    api.communityShareMinLevel = 3;
    api.userLevel.value = 1;
    await http.runWithClient(() async {
      await tester.pumpWidget(_wrap(const GalleryScreen()));
      await tester.pumpAndSettle();
    }, () => _emptyGallery);
    expect(find.textContaining('3. seviyeye ulaşınca'), findsOneWidget);
    expect(find.textContaining('1. seviyedesin'), findsOneWidget);
    expect(find.byIcon(Icons.close), findsNothing); // kilit notu kapatılamaz

    api.userLevel.value = 3; // seviye atladı
    await tester.pumpAndSettle();
    expect(find.textContaining('3. seviyeye ulaşınca'), findsNothing);
    expect(find.textContaining('Sen de paylaşabilirsin'), findsOneWidget);
    api.userLevel.value = null;
  });
}
