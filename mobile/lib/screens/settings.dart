import 'package:flutter/material.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:url_launcher/url_launcher.dart';

import '../api.dart';
import '../l10n/gen/app_localizations.dart';
import '../main.dart';

/// Ayarlar ara sayfası (müşteri isteği, 2026-08-08).
///
/// Dil, tema, yasal metinler ve geri bildirim eskiden profil ekranının altına
/// dizilmişti; Ability Chart ve Gelişim Macerası'yla birlikte tek bir uzun
/// kaydırma oluşturuyordu. Buraya alınınca profil ekranı yalnız "kim olduğun ve
/// nerede olduğun" ekranına dönüştü.
///
/// Hesap silme burada DEĞİL: tehlikeli aksiyonlar profil ekranının en altında,
/// kullanıcının bilerek gittiği yerde duruyor.
class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  Future<void> _openLegal(String path) async {
    final t = AppLocalizations.of(context);
    try {
      await launchUrl(Uri.parse('$apiBase$path'),
          mode: LaunchMode.externalApplication);
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(t.errorUnexpected)));
      }
    }
  }

  Future<void> _sendFeedback() async {
    final t = AppLocalizations.of(context);
    final info = await PackageInfo.fromPlatform();
    final uri = Uri(
      scheme: 'mailto',
      path: 'ismet17inan@gmail.com',
      query: Uri(queryParameters: {
        'subject': t.feedbackMailSubject,
        'body': t.feedbackMailBody('${info.version}+${info.buildNumber}'),
      }).query,
    );
    try {
      await launchUrl(uri);
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(t.errorUnexpected)));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(t.settingsTitle)),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Dil seçici: UI + backend hata mesajları + AI çıktı dili
          Text(t.languageTitle, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          SegmentedButton<String>(
            segments: [
              ButtonSegment(value: 'tr', label: Text(t.languageTurkish)),
              ButtonSegment(value: 'en', label: Text(t.languageEnglish)),
            ],
            selected: {ApiClient.instance.language},
            onSelectionChanged: (selection) async {
              final code = selection.first;
              try {
                await ApiClient.instance.setLanguage(code);
              } catch (e) {
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text(friendlyError(context, e))));
                }
              }
              // Backend'e yazılamasa bile yerel tercih geçerli — UI hemen döner
              appLocale.value = Locale(code);
              if (mounted) setState(() {});
            },
          ),
          const SizedBox(height: 16),
          // Karanlık tema: yalnız cihaz-yerel tercih, sunucuya yazılmaz
          SwitchListTile(
            contentPadding: EdgeInsets.zero,
            secondary: const Icon(Icons.dark_mode_outlined),
            title: Text(t.darkModeTitle),
            subtitle: Text(t.darkModeSubtitle),
            value: ApiClient.instance.darkMode,
            onChanged: (value) async {
              await ApiClient.instance.setDarkMode(value);
              appThemeMode.value = value ? ThemeMode.dark : ThemeMode.light;
              if (mounted) setState(() {});
            },
          ),
          const Divider(height: 32),
          ListTile(
            contentPadding: EdgeInsets.zero,
            leading: const Icon(Icons.feedback_outlined),
            title: Text(t.feedbackButton),
            subtitle: Text(t.sendFeedbackBody),
            onTap: _sendFeedback,
          ),
          // Yasal metinler sistem tarayıcısında açılır (webview yok).
          // App Store, EULA'nın uygulama içinden erişilebilir olmasını ister.
          ListTile(
            contentPadding: EdgeInsets.zero,
            leading: const Icon(Icons.gavel_outlined),
            title: Text(t.termsTitle),
            trailing: const Icon(Icons.open_in_new, size: 18),
            onTap: () => _openLegal('/terms'),
          ),
          ListTile(
            contentPadding: EdgeInsets.zero,
            leading: const Icon(Icons.privacy_tip_outlined),
            title: Text(t.privacyTitle),
            trailing: const Icon(Icons.open_in_new, size: 18),
            onTap: () => _openLegal('/privacy'),
          ),
        ],
      ),
    );
  }
}
