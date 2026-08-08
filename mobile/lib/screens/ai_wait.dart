import 'dart:async';

import 'package:flutter/material.dart';

import '../l10n/gen/app_localizations.dart';

/// AI çağrıları sırasında gösterilen, kapatılamayan bekleme modalı.
///
/// Neden kapatılamaz: AI çağrısı sunucuda SENKRON koşuyor (kuyruk yok) ve
/// 30-60 saniye sürebiliyor. Kullanıcı bu sırada ekrandan çıkarsa analiz
/// sunucuda tamamlanıp kaydediliyor (ölçüldü) ama istemci `mounted` kontrolü
/// yüzünden sonucu atıyor — kullanıcı redline ekranını göremiyor, çizimi
/// yalnız Gelişim Macerası'nda buluyor. Modal hem beklemeyi katlanılır
/// kılıyor hem de kazara çıkmayı engelliyor.
///
/// Kullanım:
/// ```dart
/// AiWait.show(context);
/// try {
///   final r = await ...;
/// } finally {
///   AiWait.hide(context);
/// }
/// ```
/// `hide` başka bir sayfaya geçmeden ÖNCE çağrılmalı.
class AiWait {
  const AiWait._();

  /// Modalı açar. Beklemeyi bloklamaz — dönen Future'ı await ETMEYİN.
  /// [title] verilmezse çizim analizi başlığı kullanılır.
  static void show(BuildContext context, {String? title}) {
    showDialog<void>(
      context: context,
      barrierDismissible: false,
      useRootNavigator: true,
      builder: (_) => _AiWaitDialog(title: title),
    );
  }

  /// Modalı kapatır. Açık modal yoksa hiçbir şey yapmaz (çift çağrı güvenli).
  static void hide(BuildContext context) {
    final nav = Navigator.of(context, rootNavigator: true);
    if (nav.canPop()) nav.pop();
  }
}

/// Bekleme sırasında dönüşümlü olarak değişen tek satır.
///
/// Gösterilen adımlar modelin GERÇEKTEN değerlendirdiği eksenler (bkz.
/// backend `ai/prompts.py`) — uydurma bir ilerleme çubuğu değil. Son adımda
/// durur; liste başa sarsa "bitmek üzere" hissi bozulur ve bekleyiş uzar gibi
/// görünür. Onboarding'in tam ekran bekleyişi de bunu kullanıyor.
class AiWaitTips extends StatefulWidget {
  const AiWaitTips({super.key});

  @override
  State<AiWaitTips> createState() => _AiWaitTipsState();
}

class _AiWaitTipsState extends State<AiWaitTips> {
  static const _step = Duration(seconds: 4);

  /// build()'deki ipucu listesinin uzunluğu. Sabit tutuluyor ki timer son
  /// ipucuna varınca durdurulabilsin — yoksa modal açık kaldığı sürece 4
  /// saniyede bir boşa setState çağrılır (görüntü değişmediği hâlde).
  static const _tipCount = 5;

  Timer? _timer;
  int _tip = 0;

  @override
  void initState() {
    super.initState();
    _timer = Timer.periodic(_step, (timer) {
      if (!mounted) {
        timer.cancel();
        return;
      }
      setState(() => _tip++);
      if (_tip >= _tipCount - 1) timer.cancel(); // son ipucunda dur
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final tips = [
      t.aiWaitTipProportions,
      t.aiWaitTipPerspective,
      t.aiWaitTipLight,
      t.aiWaitTipComposition,
      t.aiWaitTipWriting,
    ];
    assert(tips.length == _tipCount, 'ipucu sayısı _tipCount ile eşleşmeli');
    final tip = tips[_tip >= tips.length ? tips.length - 1 : _tip];
    // Sabit yükseklik: satır değişirken düzen zıplamasın
    return SizedBox(
      height: 40,
      child: Center(
        child: AnimatedSwitcher(
          duration: const Duration(milliseconds: 350),
          child: Text(
            tip,
            key: ValueKey(tip),
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyMedium,
          ),
        ),
      ),
    );
  }
}

class _AiWaitDialog extends StatelessWidget {
  const _AiWaitDialog({this.title});

  final String? title;

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);

    return PopScope(
      // Geri tuşu modalı kapatmasın — analiz sürerken çıkmak sonucu kaybettirir
      canPop: false,
      child: AlertDialog(
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(height: 8),
            const CircularProgressIndicator(),
            const SizedBox(height: 20),
            Text(
              title ?? t.aiWaitTitle,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            const AiWaitTips(),
            const SizedBox(height: 12),
            Text(
              t.aiWaitStayHint,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
            ),
          ],
        ),
      ),
    );
  }
}
