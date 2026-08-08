import 'package:flutter/material.dart';

import '../api.dart';
import '../l10n/gen/app_localizations.dart';
import 'redline.dart';

/// "Gelişim Macerası" — yüklenen ödevler ve AI notları, kronolojik.
///
/// Eskiden profil ekranının içinde uzun bir liste olarak duruyordu ve ekranın
/// geri kalanını (ayarlar, hesap işlemleri) aşağı itiyordu. Müşteri isteği
/// (2026-08-08): profilde kutucuk olsun, tıklayınca kendi sayfası açılsın.
/// Kendi verisini kendi çekiyor — profil ekranıyla bağı kalmadı.
class JourneyScreen extends StatefulWidget {
  const JourneyScreen({super.key});

  @override
  State<JourneyScreen> createState() => _JourneyScreenState();
}

class _JourneyScreenState extends State<JourneyScreen> {
  late Future<Map<String, dynamic>> _future;

  @override
  void initState() {
    super.initState();
    _future = ApiClient.instance.getProfile();
  }

  void _reload() => setState(() => _future = ApiClient.instance.getProfile());

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(t.journeyTitle)),
      body: FutureBuilder<Map<String, dynamic>>(
        future: _future,
        builder: (context, snap) {
          if (snap.hasError) {
            return Center(child: Text(friendlyError(context, snap.error!)));
          }
          if (!snap.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          final p = snap.data!;
          final gallery = p['gelisim_macerasi'] as List;
          final shareMinLevel = (p['community_share_min_level'] ?? 3) as int;
          final canShare = (p['level'] as int) >= shareMinLevel;

          if (gallery.isEmpty) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(32),
                child: Text(t.journeyEmpty, textAlign: TextAlign.center),
              ),
            );
          }
          return RefreshIndicator(
            onRefresh: () async => _reload(),
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Text(t.journeyHint,
                    style: Theme.of(context).textTheme.bodySmall),
                const SizedBox(height: 12),
                for (final item in gallery)
                  _JourneyCard(
                    item: item as Map<String, dynamic>,
                    canShare: canShare,
                    onChanged: _reload,
                  ),
                const SizedBox(height: 8),
                Text(
                  canShare
                      ? t.privacyKeyHint
                      : t.shareLevelLockedHint(shareMinLevel),
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _JourneyCard extends StatelessWidget {
  const _JourneyCard({
    required this.item,
    required this.canShare,
    required this.onChanged,
  });

  final Map<String, dynamic> item;
  final bool canShare;
  final VoidCallback onChanged;

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final sid = item['submission_id'] as int;
    final analysis = item['ai_result'];
    return Card(
      child: ListTile(
        leading: ClipRRect(
          borderRadius: BorderRadius.circular(6),
          child: Image.network(
            ApiClient.instance.imageUrl(sid),
            headers: ApiClient.instance.authHeaders,
            width: 48,
            height: 48,
            fit: BoxFit.cover,
            errorBuilder: (_, _, _) => const Icon(Icons.image),
          ),
        ),
        title: Text(item['node_id'] ?? t.homeworkFallback),
        subtitle: Text(
          (analysis?['overall_comment_tr'] ?? '') as String,
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
        ),
        onTap: analysis == null
            ? null
            : () => Navigator.of(context).push(MaterialPageRoute(
                  builder: (_) => RedlineScreen(
                    image: NetworkImage(
                      ApiClient.instance.imageUrl(sid),
                      headers: ApiClient.instance.authHeaders,
                    ),
                    analysis: RedlineResult.fromJson(
                        Map<String, dynamic>.from(analysis as Map)),
                    submissionId: sid,
                  ),
                )),
        trailing: Switch(
          value: item['is_public'] as bool,
          // Seviye kapısı: paylaşabilecek seviyede değilse (ve zaten herkese
          // açık değilse) anahtar kilitli.
          onChanged: (!canShare && item['is_public'] != true)
              ? null
              : (v) async {
                  try {
                    await ApiClient.instance.setPrivacy(sid, v);
                    onChanged();
                  } catch (e) {
                    if (context.mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text(friendlyError(context, e))),
                      );
                    }
                  }
                },
        ),
      ),
    );
  }
}
