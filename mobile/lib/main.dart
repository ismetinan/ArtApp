import 'package:flutter/material.dart';

import 'api.dart';
import 'l10n/gen/app_localizations.dart';
import 'screens/home_shell.dart';
import 'screens/onboarding.dart';

/// Uygulama dili. null = cihaz dilini takip et (tr dışında her şey → en).
/// Profildeki dil seçici bunu değiştirir; MaterialApp dinler ve yeniden çizer.
final ValueNotifier<Locale?> appLocale = ValueNotifier(null);

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await ApiClient.instance.loadSession();
  final saved = ApiClient.instance.savedLanguage;
  if (saved != null) appLocale.value = Locale(saved);
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
            : const HomeShell(),
      ),
    );
  }
}
