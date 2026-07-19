import 'dart:async';
import 'dart:ui';

import 'package:firebase_crashlytics/firebase_crashlytics.dart';
import 'package:flutter/material.dart';

import 'api.dart';
import 'l10n/gen/app_localizations.dart';
import 'push.dart';
import 'screens/home_shell.dart';
import 'screens/onboarding.dart';

/// Uygulama dili. null = cihaz dilini takip et (tr dışında her şey → en).
/// Profildeki dil seçici bunu değiştirir; MaterialApp dinler ve yeniden çizer.
final ValueNotifier<Locale?> appLocale = ValueNotifier(null);

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // Crashlytics: beta'da çökme görünürlüğü. Firebase yapılandırması yoksa
  // ensureFirebase false döner ve uygulama raporlamasız devam eder.
  if (await ensureFirebase()) {
    FlutterError.onError = FirebaseCrashlytics.instance.recordFlutterFatalError;
    PlatformDispatcher.instance.onError = (error, stack) {
      FirebaseCrashlytics.instance.recordError(error, stack, fatal: true);
      return true;
    };
  }
  await ApiClient.instance.loadSession();
  final saved = ApiClient.instance.savedLanguage;
  if (saved != null) appLocale.value = Locale(saved);
  unawaited(initPush()); // açılışı bloklamaz; oturum yoksa kendisi atlar
  // Abonelik lazy yenileme (Pub/Sub'sız v1): açılışta sessizce tazelenir
  if (ApiClient.instance.token != null && ApiClient.instance.billingEnabled) {
    unawaited(ApiClient.instance.getBillingStatus().catchError((_) => <String, dynamic>{}));
  }
  runApp(const ArtApp());
}

class ArtApp extends StatelessWidget {
  const ArtApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<Locale?>(
      valueListenable: appLocale,
      builder: (context, locale, _) => MaterialApp(
        title: 'Artora', // marka adı — çevrilmez
        scaffoldMessengerKey: messengerKey, // öndeyken push → SnackBar
        navigatorKey: navigatorKey, // bildirim derin bağlantıları
        locale: locale,
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        // en listede önce: desteklenmeyen cihaz dillerinde İngilizce'ye düşülür
        supportedLocales: const [Locale('en'), Locale('tr')],
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF6750A4)),
          useMaterial3: true,
        ),
        home: ApiClient.instance.token == null
            ? const WelcomeScreen()
            : const StartupGate(),
      ),
    );
  }
}

/// Açılış yönlendirmesi: oturum var ama seviye belirleme yapılmamışsa (ve
/// kullanıcı bilerek atlamadıysa) 3-resim ekranına döner — uygulamayı kapatıp
/// açmak onboarding'i atlatmaz. Profil çekilemezse (çevrimdışı) ana ekrana düşer.
class StartupGate extends StatefulWidget {
  const StartupGate({super.key});

  @override
  State<StartupGate> createState() => _StartupGateState();
}

class _StartupGateState extends State<StartupGate> {
  late final Future<bool> _needsOnboarding = _check();

  Future<bool> _check() async {
    if (ApiClient.instance.onboardingSkipped) return false;
    try {
      final profile = await ApiClient.instance.getProfile();
      return (profile['ability_chart'] as Map).isEmpty;
    } catch (_) {
      return false; // çevrimdışı/hata: kullanıcıyı kapıda bekletme
    }
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder(
      future: _needsOnboarding,
      builder: (context, snapshot) {
        if (!snapshot.hasData) {
          return const Scaffold(
              body: Center(child: CircularProgressIndicator()));
        }
        return snapshot.data! ? const PickImagesScreen() : const HomeShell();
      },
    );
  }
}
