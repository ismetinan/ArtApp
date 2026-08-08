import 'package:artapp/l10n/gen/app_localizations.dart';
import 'package:artapp/screens/ai_wait.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

Widget _wrap(Widget child, {Locale locale = const Locale('tr')}) => MaterialApp(
      locale: locale,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: const [Locale('en'), Locale('tr')],
      home: child,
    );

void main() {
  testWidgets('AI bekleme modalı açılır, ipucu satırı ilerler, kapanır',
      (tester) async {
    late BuildContext ctx;
    await tester.pumpWidget(_wrap(Builder(builder: (c) {
      ctx = c;
      return const Scaffold(body: Text('arka plan'));
    })));

    AiWait.show(ctx);
    await tester.pump(); // modal bir frame'de açılır
    await tester.pump(const Duration(milliseconds: 400));

    expect(find.text('Çizimin inceleniyor'), findsOneWidget);
    expect(find.textContaining('Oranlar ve çizgi kalitesi'), findsOneWidget);
    // Kullanıcıya çıkarsa ne olacağı söyleniyor
    expect(find.textContaining('Gelişim Macerası'), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsOneWidget);

    // 4 sn sonra ipucu değişir
    await tester.pump(const Duration(seconds: 4));
    await tester.pump(const Duration(milliseconds: 400));
    expect(find.textContaining('Perspektif ve anatomi'), findsOneWidget);

    AiWait.hide(ctx);
    await tester.pumpAndSettle();
    expect(find.text('Çizimin inceleniyor'), findsNothing);
    expect(find.text('arka plan'), findsOneWidget);
  });

  testWidgets('İpucu timer\'ı son ipucunda durur (boşa rebuild yok)',
      (tester) async {
    late BuildContext ctx;
    await tester.pumpWidget(_wrap(Builder(builder: (c) {
      ctx = c;
      return const Scaffold(body: SizedBox());
    })));

    AiWait.show(ctx);
    await tester.pump();
    // 5 ipucu × 4 sn → son ipucuna varılır ve timer iptal edilir.
    // NOT: burada pumpAndSettle KULLANILAMAZ — CircularProgressIndicator
    // sonsuz animasyon, ağaç hiçbir zaman yerine oturmaz.
    for (var i = 0; i < 5; i++) {
      await tester.pump(const Duration(seconds: 4));
    }
    await tester.pump(const Duration(milliseconds: 400));
    expect(find.textContaining('Geri bildirimin yazılıyor'), findsOneWidget);

    // Timer durduğu için modal kapandığında bekleyen timer kalmaz; kalsaydı
    // flutter_test "A Timer is still pending" hatası verirdi.
    AiWait.hide(ctx);
    await tester.pumpAndSettle();
  });

  testWidgets('Modal geri tuşuyla kapanmaz (analiz kaybını önler)',
      (tester) async {
    late BuildContext ctx;
    await tester.pumpWidget(_wrap(Builder(builder: (c) {
      ctx = c;
      return const Scaffold(body: Text('arka plan'));
    })));

    AiWait.show(ctx);
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 400));
    expect(find.text('Çizimin inceleniyor'), findsOneWidget);

    // Sistem geri tuşu
    await tester.binding.handlePopRoute();
    // pumpAndSettle yok: spinner sonsuz animasyon (yukarıdaki nota bak)
    await tester.pump(const Duration(milliseconds: 400));
    // PopScope canPop:false → modal ayakta kalmalı.
    // (Arka plan metni ağaçta zaten duruyor; modal onu kaldırmaz, üstüne biner.)
    expect(find.text('Çizimin inceleniyor'), findsOneWidget);

    AiWait.hide(ctx);
    await tester.pumpAndSettle();
  });

  testWidgets('Başlık özelleştirilebilir (ödev üretimi akışı)', (tester) async {
    late BuildContext ctx;
    await tester.pumpWidget(_wrap(Builder(builder: (c) {
      ctx = c;
      return const Scaffold(body: SizedBox());
    })));

    AiWait.show(ctx, title: 'Ödevin hazırlanıyor');
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 400));
    expect(find.text('Ödevin hazırlanıyor'), findsOneWidget);
    expect(find.text('Çizimin inceleniyor'), findsNothing);
  });

  testWidgets('hide() açık modal yokken güvenli (çift çağrı)', (tester) async {
    late BuildContext ctx;
    await tester.pumpWidget(_wrap(Builder(builder: (c) {
      ctx = c;
      return const Scaffold(body: Text('arka plan'));
    })));

    // Hiç modal açmadan hide: kök route pop edilmemeli
    AiWait.hide(ctx);
    await tester.pumpAndSettle();
    expect(find.text('arka plan'), findsOneWidget);
  });
}
