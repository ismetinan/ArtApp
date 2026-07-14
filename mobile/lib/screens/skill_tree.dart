import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:url_launcher/url_launcher.dart';

import '../api.dart';
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

  @override
  void initState() {
    super.initState();
    _future = ApiClient.instance.getTree();
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
      appBar: AppBar(title: const Text('Dersler')),
      body: FutureBuilder(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.hasError) {
            return Center(child: Text('Ağaç yüklenemedi: ${snapshot.error}'));
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
              ? () => ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                  content:
                      Text('Bu ders için önce önceki dersleri tamamlaman gerekiyor.')))
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
                Text('${axisLabels[node.skillAxis]} • ${node.xpReward} XP',
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
            imagePath: file.path,
            analysis: result.analysis,
            xpAwarded: result.xpAwarded,
          ),
        ));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('Yükleme başarısız: $e')));
      }
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final node = widget.node;
    final hasVideo =
        node.youtubeVideoId.isNotEmpty && node.youtubeVideoId != 'PLACEHOLDER';
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
            Card(
              child: ListTile(
                leading: const Icon(Icons.ondemand_video),
                title: Text(hasVideo ? 'Ders videosunu izle' : 'Video yakında'),
                subtitle: Text(node.description),
                onTap: hasVideo
                    ? () => launchUrl(
                        Uri.parse('https://youtu.be/${node.youtubeVideoId}'))
                    : null,
              ),
            ),
            const SizedBox(height: 16),
            Text('Ödevini yükle',
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            const Text(
                'Videoyu izledikten sonra çalışmanı yükle; saniyeler içinde '
                'yapıcı bir redline analizi alacaksın.'),
            const SizedBox(height: 16),
            if (_submitting)
              const Center(child: CircularProgressIndicator())
            else ...[
              FilledButton.icon(
                icon: const Icon(Icons.folder),
                label: const Text('Cihazdan Seç ve Gönder'),
                onPressed: () => _submit(ImageSource.gallery),
              ),
              const SizedBox(height: 8),
              OutlinedButton.icon(
                icon: const Icon(Icons.camera_alt),
                label: const Text('Kamera ile Çek ve Gönder'),
                onPressed: () => _submit(ImageSource.camera),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
