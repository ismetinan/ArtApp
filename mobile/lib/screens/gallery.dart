import 'package:flutter/material.dart';

import '../api.dart';
import '../l10n/gen/app_localizations.dart';

/// Topluluk sekmesi (Faz 3): herkese açık paylaşılan çizimlerin akışı.
/// Kaynak: Gelişim Macerası'ndaki gizlilik anahtarıyla "açık" yapılan işler.
class GalleryScreen extends StatefulWidget {
  const GalleryScreen({super.key});

  @override
  State<GalleryScreen> createState() => _GalleryScreenState();
}

class _GalleryScreenState extends State<GalleryScreen> {
  late Future<List<GalleryItem>> _future;

  @override
  void initState() {
    super.initState();
    _future = ApiClient.instance.getGallery();
  }

  void _refresh() => setState(() => _future = ApiClient.instance.getGallery());

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(
        title: Text(t.tabGallery),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _refresh),
        ],
      ),
      body: FutureBuilder<List<GalleryItem>>(
        future: _future,
        builder: (context, snap) {
          if (snap.hasError) {
            return Center(child: Text(friendlyError(context, snap.error!)));
          }
          if (!snap.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          final items = snap.data!;
          if (items.isEmpty) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text(t.galleryEmpty, textAlign: TextAlign.center),
              ),
            );
          }
          return RefreshIndicator(
            onRefresh: () async => _refresh(),
            child: GridView.builder(
              padding: const EdgeInsets.all(12),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 2,
                crossAxisSpacing: 12,
                mainAxisSpacing: 12,
                childAspectRatio: 0.8,
              ),
              itemCount: items.length,
              itemBuilder: (context, i) => _GalleryCard(item: items[i]),
            ),
          );
        },
      ),
    );
  }
}

class _GalleryCard extends StatelessWidget {
  final GalleryItem item;
  const _GalleryCard({required this.item});

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: () => Navigator.of(context).push(
          MaterialPageRoute(builder: (_) => _GalleryDetailScreen(item: item)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: Ink.image(
                image: NetworkImage(
                    ApiClient.instance.imageUrl(item.submissionId),
                    headers: ApiClient.instance.authHeaders),
                fit: BoxFit.cover,
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(item.displayName,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.labelLarge),
                  Text(item.nodeTitle ?? t.freeAnalysisTitle,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.bodySmall),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _GalleryDetailScreen extends StatelessWidget {
  final GalleryItem item;
  const _GalleryDetailScreen({required this.item});

  /// UGC moderasyonu (Play politikası): sebep seç → şikayet gönder.
  Future<void> _report(BuildContext context) async {
    final t = AppLocalizations.of(context);
    final reasons = {
      'uygunsuz': t.reportReasonUygunsuz,
      'spam': t.reportReasonSpam,
      'telif': t.reportReasonTelif,
      'diger': t.reportReasonDiger,
    };
    final reason = await showModalBottomSheet<String>(
      context: context,
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Padding(
              padding: const EdgeInsets.all(16),
              child: Text(t.reportSheetTitle,
                  style: Theme.of(ctx).textTheme.titleMedium),
            ),
            for (final e in reasons.entries)
              ListTile(
                title: Text(e.value),
                onTap: () => Navigator.pop(ctx, e.key),
              ),
          ],
        ),
      ),
    );
    if (reason == null || !context.mounted) return;
    try {
      await ApiClient.instance.reportSubmission(item.submissionId, reason);
      if (context.mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(t.reportThanks)));
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(friendlyError(context, e))));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(
        title: Text(item.displayName),
        actions: [
          if (!item.isMine)
            IconButton(
              icon: const Icon(Icons.flag_outlined),
              tooltip: t.reportButton,
              onPressed: () => _report(context),
            ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(12),
            child: Image.network(
              ApiClient.instance.imageUrl(item.submissionId),
              headers: ApiClient.instance.authHeaders,
              fit: BoxFit.contain,
            ),
          ),
          const SizedBox(height: 12),
          Text(item.nodeTitle ?? t.freeAnalysisTitle,
              style: Theme.of(context).textTheme.titleMedium),
          Text(item.createdAt.split('T').first,
              style: Theme.of(context).textTheme.bodySmall),
        ],
      ),
    );
  }
}
