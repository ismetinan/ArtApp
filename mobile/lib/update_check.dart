import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';

import 'api.dart';
import 'l10n/gen/app_localizations.dart';

/// "1.10.0" > "1.9.2" gibi sürüm adı karşılaştırması. Eksik parçalar 0
/// sayılır ("1.1" == "1.1.0"); sayısal olmayan parça 0'a düşer.
int compareVersions(String a, String b) {
  List<int> parts(String v) =>
      v.split('+').first.split('.').map((p) => int.tryParse(p) ?? 0).toList();
  final x = parts(a), y = parts(b);
  for (var i = 0; i < 3; i++) {
    final d = (i < x.length ? x[i] : 0) - (i < y.length ? y[i] : 0);
    if (d != 0) return d.sign;
  }
  return 0;
}

/// Sunucudaki eşiklere göre güncelleme uyarısı (bkz. backend /app-config).
/// - min_version altı: kapatılamayan "güncellemen gerekiyor" diyaloğu
/// - latest_version altı: kapatılabilir öneri, aynı sürüm için bir kez
/// Ağ hatası ya da eksik bilgi hiçbir zaman kullanıcıyı engellemez.
Future<void> checkForUpdate(BuildContext context) async {
  final current = ApiClient.instance.appVersion.split('+').first;
  if (current.isEmpty) return;
  Map<String, dynamic> cfg;
  try {
    final platform = Platform.isIOS ? 'ios' : 'android';
    final r = await http
        .get(Uri.parse('$apiBase/app-config?platform=$platform'))
        .timeout(const Duration(seconds: 8));
    if (r.statusCode != 200) return;
    cfg = jsonDecode(utf8.decode(r.bodyBytes)) as Map<String, dynamic>;
  } catch (_) {
    return;
  }
  final min = cfg['min_version'] as String?;
  final latest = cfg['latest_version'] as String?;
  final store = cfg['store_url'] as String?;
  if (store == null || !context.mounted) return;

  if (min != null && compareVersions(current, min) < 0) {
    await _showUpdateDialog(context, store, required: true);
    return;
  }
  if (latest != null && compareVersions(current, latest) < 0) {
    final key = 'update_dismissed_$latest';
    try {
      final prefs = await SharedPreferences.getInstance();
      if (prefs.getBool(key) ?? false) return;
      if (!context.mounted) return;
      final later = await _showUpdateDialog(context, store, required: false);
      if (later) await prefs.setBool(key, true);
    } catch (_) {/* tercih okunamadıysa öneriyi atla */}
  }
}

/// true = kullanıcı "Sonra" dedi.
Future<bool> _showUpdateDialog(BuildContext context, String storeUrl,
    {required bool required}) async {
  final t = AppLocalizations.of(context);
  Future<void> openStore() =>
      launchUrl(Uri.parse(storeUrl), mode: LaunchMode.externalApplication);
  final later = await showDialog<bool>(
    context: context,
    barrierDismissible: !required,
    builder: (ctx) => PopScope(
      canPop: !required,
      child: AlertDialog(
        icon: const Icon(Icons.system_update, size: 36),
        title: Text(required ? t.updateRequiredTitle : t.updateAvailableTitle),
        content: Text(required ? t.updateRequiredBody : t.updateAvailableBody),
        actions: [
          if (!required)
            TextButton(
              onPressed: () => Navigator.of(ctx).pop(true),
              child: Text(t.updateLater),
            ),
          FilledButton(
            // Zorunluda diyalog açık kalır: mağazadan dönen kullanıcı hâlâ
            // güncellemediyse uygulamayı kullanamaz
            onPressed: () async {
              await openStore();
              if (!required && ctx.mounted) Navigator.of(ctx).pop(false);
            },
            child: Text(t.updateNow),
          ),
        ],
      ),
    ),
  );
  return later ?? false;
}
