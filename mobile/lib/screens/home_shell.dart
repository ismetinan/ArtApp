import 'package:flutter/material.dart';

import '../api.dart';
import '../l10n/gen/app_localizations.dart';
import '../push.dart';
import '../update_check.dart';
import 'badges.dart';
import 'gallery.dart';
import 'mentors.dart';
import 'profile.dart';
import 'skill_tree.dart' show SkillTreeScreen, freeAnalysisBusy, freeAnalysisTrigger;

/// Ana navigasyon: Mentorlar | Dersler | Topluluk | Profil
/// (CLAUDE.md §7.1 + Faz 3 topluluk galerisi)
class HomeShell extends StatefulWidget {
  const HomeShell({super.key});

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _index = 1; // açılışta Dersler

  @override
  void initState() {
    super.initState();
    // Girişten sonra ana ekrana her varışta token kaydı tazelenir
    initPush();
    ApiClient.instance.celebrations.addListener(_onCelebration);
    // Dinleyici bağlanmadan önce düşmüş bir kutlama olabilir
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _onCelebration();
      // Sunucu eşiklerine göre güncelleme uyarısı (öneri ya da zorunlu)
      if (mounted) checkForUpdate(context);
    });
  }

  @override
  void dispose() {
    ApiClient.instance.celebrations.removeListener(_onCelebration);
    super.dispose();
  }

  bool _celebrating = false;

  /// Rozet/kampanya kutlaması: hangi ekran profili yüklerse yüklesin burada
  /// bir kez gösterilir. Diyalog açıkken gelen yenisi kapanınca gösterilir.
  Future<void> _onCelebration() async {
    final notifier = ApiClient.instance.celebrations;
    if (_celebrating || notifier.value == null || !mounted) return;
    final c = notifier.value!;
    notifier.value = null;
    _celebrating = true;
    await showCelebration(context, c);
    _celebrating = false;
    if (mounted) _onCelebration();
  }

  /// Ability Chart'tan gelen yönlendirme: ilgili eksenin dersine odaklan
  String? _focusAxis;

  void goToLessons(String axis) {
    setState(() {
      _focusAxis = axis;
      _index = 1;
    });
  }

  @override
  Widget build(BuildContext context) {
    final screens = [
      const MentorsScreen(),
      SkillTreeScreen(focusAxis: _focusAxis, key: ValueKey(_focusAxis)),
      const GalleryScreen(),
      ProfileScreen(onAxisTap: goToLessons),
    ];
    final t = AppLocalizations.of(context);
    // Alt çubuk: Mentorlar | Dersler | [AI] | Topluluk | Profil. Ortadaki
    // boşluk devre dışı bir yer tutucu hedef; AI butonu onun üstüne biner.
    // Çubuk indeksi (0-4) ↔ ekran indeksi (0-3) dönüşümü aşağıda.
    int toBar(int screen) => screen >= 2 ? screen + 1 : screen;
    int toScreen(int bar) => bar > 2 ? bar - 1 : bar;
    return Scaffold(
      body: IndexedStack(index: _index, children: screens),
      floatingActionButton: const _AiAnalysisButton(),
      floatingActionButtonLocation: const _InBarCenterLocation(),
      bottomNavigationBar: NavigationBar(
        selectedIndex: toBar(_index),
        onDestinationSelected: (bar) {
          if (bar == 2) return; // yer tutucu
          setState(() {
            _index = toScreen(bar);
            if (_index != 1) _focusAxis = null;
          });
        },
        destinations: [
          NavigationDestination(
              icon: const Icon(Icons.people), label: t.tabMentors),
          NavigationDestination(
              icon: const Icon(Icons.account_tree), label: t.tabLessons),
          const NavigationDestination(
              enabled: false, icon: SizedBox(width: 56), label: ''),
          NavigationDestination(
              icon: const Icon(Icons.photo_library), label: t.tabGallery),
          NavigationDestination(
              icon: const Icon(Icons.person), label: t.tabProfile),
        ],
      ),
    );
  }
}


/// Alt çubuğun ortasındaki serbest AI analizi butonu: diğer sekmelerden
/// büyük, dış halkalı yuvarlak. Akışın kendisi ders ekranında (bkz.
/// skill_tree.dart freeAnalysisTrigger); analiz sürerken spinner gösterir.
class _AiAnalysisButton extends StatelessWidget {
  const _AiAnalysisButton();

  static const double size = 64;
  static const double ring = 5;

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final t = AppLocalizations.of(context);
    return ValueListenableBuilder<bool>(
      valueListenable: freeAnalysisBusy,
      builder: (context, busy, _) => Tooltip(
        message: t.freeAnalysisTitle,
        child: Semantics(
          button: true,
          label: t.freeAnalysisTitle,
          child: Container(
            width: size + ring * 2,
            height: size + ring * 2,
            padding: const EdgeInsets.all(ring),
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              // Dış katman: çubuğun zeminiyle aynı renk bir halka + ince
              // vurgu kenarı — buton çubuktan "yükselmiş" görünür
              color: cs.surfaceContainer,
              border: Border.all(color: cs.primary.withValues(alpha: 0.35), width: 1.5),
              boxShadow: [
                BoxShadow(
                  color: cs.shadow.withValues(alpha: 0.18),
                  blurRadius: 8,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: Material(
              shape: const CircleBorder(),
              color: cs.primary,
              clipBehavior: Clip.antiAlias,
              child: InkWell(
                onTap: busy ? null : () => freeAnalysisTrigger.value++,
                child: Center(
                  child: busy
                      ? SizedBox(
                          width: 24,
                          height: 24,
                          child: CircularProgressIndicator(
                              strokeWidth: 2.5, color: cs.onPrimary),
                        )
                      : Icon(Icons.auto_awesome, size: 30, color: cs.onPrimary),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Butonu yatayda tam ortaya, dikeyde çubuğun ikon sırasına hizalar; üst
/// kenardan biraz taşar ki sekmelerden ayrı, birincil aksiyon olduğu belli olsun.
class _InBarCenterLocation extends FloatingActionButtonLocation {
  const _InBarCenterLocation();

  @override
  Offset getOffset(ScaffoldPrelayoutGeometry g) {
    final x = (g.scaffoldSize.width - g.floatingActionButtonSize.width) / 2;
    // contentBottom = alt çubuğun üst kenarı. Butonun ~%35'i çubuğun üstünde.
    final y = g.contentBottom - g.floatingActionButtonSize.height * 0.35;
    return Offset(x, y);
  }
}
