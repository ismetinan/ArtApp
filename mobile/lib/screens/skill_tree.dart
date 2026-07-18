import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:url_launcher/url_launcher.dart';

import '../api.dart';
import '../l10n/gen/app_localizations.dart';
import 'redline.dart';

/// Dersler sekmesi: düğüm tabanlı yetenek ağacı (CLAUDE.md §7.4).
/// Düğümler önkoşul derinliğine göre katmanlanır, aralarındaki bağlar çizilir.
class SkillTreeScreen extends StatefulWidget {
  /// Ability Chart'tan tıklanarak gelindiyse vurgulanacak eksen
  final String? focusAxis;
  const SkillTreeScreen({super.key, this.focusAxis});

  @override
  State<SkillTreeScreen> createState() => _SkillTreeScreenState();
}

class _SkillTreeScreenState extends State<SkillTreeScreen> {
  late Future<List<SkillNode>> _future;
  Locale? _lastLocale;

  @override
  void initState() {
    super.initState();
    _future = ApiClient.instance.getTree();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // Ders başlıkları sunucudan seçili dilde gelir; uygulama içi dil seçici
    // kullanılınca ağacı yeni dille yeniden çek (yoksa eski dil ekranda kalır).
    final locale = Localizations.localeOf(context);
    if (_lastLocale != null && _lastLocale != locale) {
      _future = ApiClient.instance.getTree();
    }
    _lastLocale = locale;
  }

  void _reload() => setState(() => _future = ApiClient.instance.getTree());

  int _depth(SkillNode node, Map<String, SkillNode> byId, [int guard = 0]) {
    if (node.prerequisites.isEmpty || guard > 20) return 0;
    return 1 +
        node.prerequisites
            .map((p) => _depth(byId[p]!, byId, guard + 1))
            .reduce((a, b) => a > b ? a : b);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(AppLocalizations.of(context).tabLessons)),
      body: FutureBuilder(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.hasError) {
            return Center(
                child: Text(AppLocalizations.of(context)
                    .treeLoadError('${snapshot.error}')));
          }
          if (!snapshot.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          final nodes = snapshot.data!;
          final byId = {for (final n in nodes) n.id: n};
          final rows = <int, List<SkillNode>>{};
          for (final n in nodes) {
            rows.putIfAbsent(_depth(n, byId), () => []).add(n);
          }
          final depths = rows.keys.toList()..sort();
          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                for (final d in depths) ...[
                  if (d > 0)
                    const Padding(
                      padding: EdgeInsets.symmetric(vertical: 4),
                      child: Icon(Icons.arrow_downward, size: 20),
                    ),
                  Wrap(
                    spacing: 12,
                    runSpacing: 12,
                    alignment: WrapAlignment.center,
                    children: [
                      for (final n in rows[d]!)
                        _NodeCard(
                          node: n,
                          highlighted: n.skillAxis == widget.focusAxis,
                          onCompleted: _reload,
                        ),
                    ],
                  ),
                ],
              ],
            ),
          );
        },
      ),
    );
  }
}

class _NodeCard extends StatelessWidget {
  final SkillNode node;
  final bool highlighted;
  final VoidCallback onCompleted;
  const _NodeCard(
      {required this.node, required this.highlighted, required this.onCompleted});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final locked = node.status == 'locked';
    final completed = node.status == 'completed';
    return SizedBox(
      width: 160,
      child: Card(
        color: highlighted
            ? scheme.tertiaryContainer
            : completed
                ? scheme.primaryContainer
                : locked
                    ? scheme.surfaceContainerHighest
                    : null,
        child: InkWell(
          onTap: locked
              ? () => ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                  content: Text(AppLocalizations.of(context).lockedSnack)))
              : () async {
                  final changed = await Navigator.of(context).push<bool>(
                    MaterialPageRoute(builder: (_) => NodeDetailScreen(node: node)),
                  );
                  if (changed == true) onCompleted();
                },
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              children: [
                Icon(
                  completed
                      ? Icons.check_circle
                      : locked
                          ? Icons.lock
                          : Icons.play_circle,
                  color: completed ? scheme.primary : null,
                ),
                const SizedBox(height: 8),
                Text(node.title,
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.titleSmall),
                const SizedBox(height: 4),
                Text(
                    AppLocalizations.of(context).nodeMeta(
                        axisLabels(AppLocalizations.of(context))[node.skillAxis] ??
                            node.skillAxis,
                        node.xpReward),
                    style: Theme.of(context).textTheme.bodySmall),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

/// Düğüm detayı: video + ödev yükleme (+ "ders sor" Faz 2'de mentora bağlanacak)
class NodeDetailScreen extends StatefulWidget {
  final SkillNode node;
  const NodeDetailScreen({super.key, required this.node});

  @override
  State<NodeDetailScreen> createState() => _NodeDetailScreenState();
}

class _NodeDetailScreenState extends State<NodeDetailScreen> {
  bool _submitting = false;
  bool _completedNow = false;

  Future<void> _submit(ImageSource source) async {
    final file = await ImagePicker().pickImage(source: source, maxWidth: 1600);
    if (file == null) return;
    setState(() => _submitting = true);
    try {
      final result = await ApiClient.instance
          .submitAssignment(widget.node.id, await file.readAsBytes(), file.name);
      _completedNow = true;
      if (mounted) {
        await Navigator.of(context).push(MaterialPageRoute(
          builder: (_) => RedlineScreen(
            image: FileImage(File(file.path)),
            analysis: result.analysis,
            xpAwarded: result.xpAwarded,
            submissionId: result.submissionId,
          ),
        ));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(friendlyError(context, e))));
      }
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final node = widget.node;
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop) Navigator.of(context).pop(_completedNow);
      },
      child: Scaffold(
        appBar: AppBar(title: Text(node.title)),
        body: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text(node.description),
            const SizedBox(height: 12),
            if (node.resources.isEmpty)
              Card(
                child: ListTile(
                  leading: const Icon(Icons.ondemand_video),
                  title: Text(AppLocalizations.of(context).videoSoon),
                  subtitle: Text(AppLocalizations.of(context).videoSoonBody),
                ),
              )
            else
              for (final r in node.resources)
                Card(
                  child: ListTile(
                    leading: Icon(
                        r.isPlaylist ? Icons.playlist_play : Icons.play_circle),
                    title: Text(r.title),
                    subtitle: Text(AppLocalizations.of(context).resourceMeta(
                        r.author,
                        r.isPlaylist
                            ? AppLocalizations.of(context).resourceKindPlaylist
                            : AppLocalizations.of(context).resourceKindVideo)),
                    trailing: const Icon(Icons.open_in_new, size: 18),
                    onTap: () => launchUrl(r.url),
                  ),
                ),
            const SizedBox(height: 16),
            Text(AppLocalizations.of(context).uploadHomework,
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            Text(AppLocalizations.of(context).uploadHint),
            const SizedBox(height: 16),
            if (_submitting)
              const Center(child: CircularProgressIndicator())
            else ...[
              FilledButton.icon(
                icon: const Icon(Icons.folder),
                label: Text(AppLocalizations.of(context).submitFromDevice),
                onPressed: () => _submit(ImageSource.gallery),
              ),
              const SizedBox(height: 8),
              OutlinedButton.icon(
                icon: const Icon(Icons.camera_alt),
                label: Text(AppLocalizations.of(context).submitFromCamera),
                onPressed: () => _submit(ImageSource.camera),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
