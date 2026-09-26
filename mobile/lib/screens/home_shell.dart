import 'package:flutter/material.dart';

import '../api.dart';
import '../l10n/gen/app_localizations.dart';
import '../push.dart';
import 'badges.dart';
import 'gallery.dart';
import 'mentors.dart';
import 'profile.dart';
import 'skill_tree.dart';

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
    WidgetsBinding.instance.addPostFrameCallback((_) => _onCelebration());
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
    return Scaffold(
      body: IndexedStack(index: _index, children: screens),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (i) => setState(() {
          _index = i;
          if (i != 1) _focusAxis = null;
        }),
        destinations: [
          NavigationDestination(
              icon: const Icon(Icons.people),
              label: AppLocalizations.of(context).tabMentors),
          NavigationDestination(
              icon: const Icon(Icons.account_tree),
              label: AppLocalizations.of(context).tabLessons),
          NavigationDestination(
              icon: const Icon(Icons.photo_library),
              label: AppLocalizations.of(context).tabGallery),
          NavigationDestination(
              icon: const Icon(Icons.person),
              label: AppLocalizations.of(context).tabProfile),
        ],
      ),
    );
  }
}
