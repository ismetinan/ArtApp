import 'dart:convert';

import 'package:artapp/api.dart';
import 'package:artapp/l10n/gen/app_localizations.dart';
import 'package:artapp/screens/gallery.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

GalleryItem _item({bool mine = false, int likes = 3, bool liked = false}) =>
    GalleryItem.fromJson({
      'submission_id': 7,
      'display_name': 'Çizer',
      'node_title': 'Ders',
      'is_mine': mine,
      'created_at': '2026-10-11T10:00:00',
      'like_count': likes,
      'liked_by_me': liked,
    });

Future<void> _pump(WidgetTester tester, GalleryItem item, MockClient client) async {
  await http.runWithClient(() async {
    await tester.pumpWidget(MaterialApp(
      locale: const Locale('tr'),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: const [Locale('en'), Locale('tr')],
      home: Scaffold(body: Center(child: LikeButton(item: item))),
    ));
  }, () => client);
}

void main() {
  setUp(() => ApiClient.instance.token = 't');

  testWidgets('Beğen: sayı artar, kalp dolar, sunucu sayısı esas alınır', (tester) async {
    String? method;
    final client = MockClient((req) async {
      method = req.method;
      return http.Response(jsonEncode({'like_count': 5, 'liked_by_me': true}), 200);
    });
    final item = _item();
    await _pump(tester, item, client);
    expect(find.text('3'), findsOneWidget);
    await http.runWithClient(() async {
      await tester.tap(find.byIcon(Icons.favorite_border));
      await tester.pumpAndSettle();
    }, () => client);
    expect(method, 'PUT');
    expect(find.byIcon(Icons.favorite), findsOneWidget);
    expect(find.text('5'), findsOneWidget); // başkaları da beğenmiş
    expect(item.likedByMe, isTrue);
  });

  testWidgets('Hata olursa iyimser değişiklik geri alınır', (tester) async {
    final client = MockClient((_) async => http.Response('{"detail":"x"}', 500));
    final item = _item(liked: true, likes: 4);
    await _pump(tester, item, client);
    await http.runWithClient(() async {
      await tester.tap(find.byIcon(Icons.favorite));
      await tester.pumpAndSettle();
    }, () => client);
    expect(item.likedByMe, isTrue);
    expect(find.text('4'), findsOneWidget);
  });

  testWidgets('Kendi çizimi: yalnız sayı, dokununca istek gitmez', (tester) async {
    var calls = 0;
    final client = MockClient((_) async {
      calls++;
      return http.Response('{}', 200);
    });
    await _pump(tester, _item(mine: true, likes: 2), client);
    await tester.tap(find.text('2'));
    await tester.pumpAndSettle();
    expect(calls, 0);
    expect(find.text('2'), findsOneWidget);
  });
}
