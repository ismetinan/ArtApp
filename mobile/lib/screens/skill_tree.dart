import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:url_launcher/url_launcher.dart';

import '../api.dart';
import '../l10n/gen/app_localizations.dart';
import '../analysis_watcher.dart';
import '../pending_analysis.dart';
import 'ai_wait.dart';
import 'redline.dart';
import 'store.dart';

/// Dersler sekmesi: düğüm tabanlı yetenek ağacı (CLAUDE.md §7.4).
/// Düğümler önkoşul derinliğine göre katmanlanır, aralarındaki bağlar çizilir.
class SkillTreeScreen extends StatefulWidget {
  /// Ability Chart'tan tıklanarak gelindiyse vurgulanacak eksen
  final String? focusAxis;
  const SkillTreeScreen({super.key, this.focusAxis});

  @override
  State<SkillTreeScreen> createState() => _SkillTreeScreenState();
}

class _SkillTreeScreenState extends State<SkillTreeScreen>
    with WidgetsBindingObserver {
  late Future<({List<SkillNode> nodes, String? recommendedNodeId})> _future;
  Locale? _lastLocale;
  bool _freeBusy = false;
  bool _recovering = false;

  @override
  void initState() {
    super.initState();
    _future = ApiClient.instance.getTree();
    // Android seçici/analiz sırasında uygulamayı öldürdüyse kurtarma
    WidgetsBinding.instance.addObserver(this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _recoverPending();
      _recoverJob();
    });
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _recoverPending();
      _recoverJob();
    }
  }

  /// Yarım kalmış analizi kurtarır (bkz. lib/pending_analysis.dart).
  ///
  /// - `picking`: seçici sırasında ölmüşüz → fotoğrafı geri al, kullanıcıya
  ///   sessizce kaybettirme.
  /// - `uploading`: analiz sunucuda tamamlanıp kaydedilmiş olabilir → kullanıcıyı
  ///   tekrar jeton harcamaya bırakmadan sonucun nerede olduğunu söyle.
  Future<void> _recoverPending() async {
    if (_recovering || _freeBusy) return;
    final pending = await PendingAnalysis.read();
    if (pending == null || !mounted) return;
    _recovering = true;
    try {
      if (pending.stage == PendingAnalysis.stagePicking) {
        final file = await PendingAnalysis.recoverLostImage();
        await PendingAnalysis.clear();
        if (file == null || !mounted) return;
        if (pending.nodeId == PendingAnalysis.freeAnalysisNode) {
          await _sendFreeAnalysis(file);
        } else {
          // Düğüm ekranı yeniden kurulamadığı için serbest analiz olarak
          // sürdürmek yanlış olurdu; kullanıcıya seçimini kaybetmediğini
          // söyleyip tekrar denemesini istiyoruz.
          if (mounted) {
            final t = AppLocalizations.of(context);
            ScaffoldMessenger.of(context)
                .showSnackBar(SnackBar(content: Text(t.recoveredPickRetry)));
          }
        }
        return;
      }
      await PendingAnalysis.clear();
    } finally {
      _recovering = false;
    }
  }

  /// Yarım kalmış analiz İŞİNİ kurtarır (Faz 2).
  ///
  /// Uygulama analiz sırasında kapansa bile iş sunucuda koşmaya devam ediyor;
  /// burada ya bitmiş sonucu gösteriyoruz ya da beklemeyi kaldığı yerden
  /// sürdürüyoruz. Kullanıcı tekrar yükleyip ikinci kez jeton harcamıyor.
  Future<void> _recoverJob() async {
    if (_recovering || _freeBusy) return;
    _recovering = true;
    try {
      final job = await AnalysisWatcher.recover();
      if (job == null || !mounted) return;
      if (job.isFinished) {
        if (job.status == 'done' && job.analysis != null) {
          await _showRecovered(job);
        } else if (job.status == 'failed' && mounted) {
          final t = AppLocalizations.of(context);
          ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text(job.error ?? t.errorUnexpected)));
        }
        return;
      }
      // Hâlâ koşuyor: beklemeyi sürdür
      await _awaitJob(job.jobId);
    } catch (_) {
      // Kurtarma en iyi çabadır; ağ yoksa sessizce geç
    } finally {
      _recovering = false;
    }
  }

  Future<void> _showRecovered(AnalysisJobInfo job) async {
    if (!mounted || job.submissionId == null) return;
    await Navigator.of(context).push(MaterialPageRoute(
      builder: (_) => RedlineScreen(
        // Yerel dosya yok (uygulama yeniden başladı) — çizim sunucudan
        image: NetworkImage(
          ApiClient.instance.imageUrl(job.submissionId!),
          headers: ApiClient.instance.authHeaders,
        ),
        analysis: job.analysis!,
        xpAwarded: job.xpAwarded,
        submissionId: job.submissionId,
      ),
    ));
    if (mounted) _reload();
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

  /// Serbest çizim analizi: ders dışı bitmiş bir işi yükle → redline al.
  Future<void> _freeAnalysis() async {
    await PendingAnalysis.mark(
        PendingAnalysis.freeAnalysisNode, PendingAnalysis.stagePicking);
    final file =
        await ImagePicker().pickImage(source: ImageSource.gallery, maxWidth: 1600);
    if (file == null || !mounted) {
      await PendingAnalysis.clear();
      return;
    }
    await _sendFreeAnalysis(file);
  }

  Future<void> _sendFreeAnalysis(XFile file) async {
    if (!mounted) return;
    setState(() => _freeBusy = true);
    await PendingAnalysis.clear(); // seçim tamam, artık iş kimliği takip ediyor
    if (!mounted) return;

    int jobId;
    try {
      jobId = await ApiClient.instance
          .submitFreeAnalysisAsync(await file.readAsBytes(), file.name);
    } catch (e) {
      if (!mounted) return;
      setState(() => _freeBusy = false);
      // Jeton yetersizse (402) ve mağaza açıksa "Jeton Al" kısayolu eklenir.
      showErrorWithStoreAction(context, e);
      return;
    }
    await AnalysisWatcher.remember(jobId);
    if (!mounted) return;
    await _awaitJob(jobId, image: FileImage(File(file.path)));
    if (mounted) setState(() => _freeBusy = false);
  }

  /// İşi bekler ve sonucu gösterir. Bekleme modalı burada açılıp kapanıyor;
  /// modal artık ZORUNLU değil — iş sunucuda koştuğu için kullanıcı çıksa da
  /// sonuç kaybolmaz, ama akışta kalması hâlâ en iyi deneyim.
  Future<void> _awaitJob(int jobId, {ImageProvider? image}) async {
    AiWait.show(context);
    AnalysisJobInfo job;
    try {
      job = await AnalysisWatcher.waitFor(jobId);
    } catch (e) {
      if (!mounted) return;
      AiWait.hide(context);
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(friendlyError(context, e))));
      return;
    }
    if (!mounted) return;
    AiWait.hide(context);

    if (job.status == 'failed') {
      final t = AppLocalizations.of(context);
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(job.error ?? t.errorUnexpected)));
      return;
    }
    if (job.status != 'done' || job.analysis == null) {
      // İstemci zaman aşımı — iş sunucuda sürüyor, sonuç kaybolmuyor
      final t = AppLocalizations.of(context);
      ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(t.analysisStillRunning), duration: const Duration(seconds: 6)));
      return;
    }
    // Kurtarma yolunda yerel dosya elimizde yok (uygulama yeniden başladı) —
    // çizimi sunucudan çekiyoruz.
    final shown = image ??
        NetworkImage(
          ApiClient.instance.imageUrl(job.submissionId!),
          headers: ApiClient.instance.authHeaders,
        );
    await Navigator.of(context).push(MaterialPageRoute(
      builder: (_) => RedlineScreen(
        image: shown,
        analysis: job.analysis!,
        xpAwarded: job.xpAwarded,
        submissionId: job.submissionId,
      ),
    ));
    if (mounted) _reload(); // ağaç ilerlemesi değişmiş olabilir
  }

  int _depth(SkillNode node, Map<String, SkillNode> byId, [int guard = 0]) {
    if (node.prerequisites.isEmpty || guard > 20) return 0;
    return 1 +
        node.prerequisites
            .map((p) => _depth(byId[p]!, byId, guard + 1))
            .reduce((a, b) => a > b ? a : b);
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(
        title: Text(t.tabLessons),
        actions: [
          _freeBusy
              ? const Padding(
                  padding: EdgeInsets.all(14),
                  child: SizedBox(
                      width: 20, height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2)),
                )
              : IconButton(
                  icon: const Icon(Icons.auto_awesome),
                  tooltip: t.freeAnalysisTitle,
                  onPressed: _freeAnalysisSheet,
                ),
        ],
      ),
      body: FutureBuilder(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.hasError) {
            return Center(child: Text(t.treeLoadError('${snapshot.error}')));
          }
          if (!snapshot.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          final nodes = snapshot.data!.nodes;
          final recommendedId = snapshot.data!.recommendedNodeId;
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
                // Kendi kursuyla ilerleyenler için çerçeve notu (müşteri isteği)
                Card(
                  color: Theme.of(context).colorScheme.surfaceContainerHighest,
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Row(
                      children: [
                        const Icon(Icons.info_outline, size: 20),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(t.ownCourseNote,
                              style: Theme.of(context).textTheme.bodySmall),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 12),
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
                          recommended: n.id == recommendedId,
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

  void _freeAnalysisSheet() {
    final t = AppLocalizations.of(context);
    showModalBottomSheet<void>(
      context: context,
      builder: (ctx) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(t.freeAnalysisTitle,
                  style: Theme.of(ctx).textTheme.titleMedium),
              const SizedBox(height: 8),
              Text(t.freeAnalysisHint),
              const SizedBox(height: 16),
              FilledButton.icon(
                icon: const Icon(Icons.folder),
                label: Text(t.submitFromDevice),
                onPressed: () {
                  Navigator.pop(ctx);
                  _freeAnalysis();
                },
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _NodeCard extends StatelessWidget {
  final SkillNode node;
  final bool highlighted;
  final bool recommended;
  final VoidCallback onCompleted;
  const _NodeCard({
    required this.node,
    required this.highlighted,
    required this.recommended,
    required this.onCompleted,
  });

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
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
              ? () => ScaffoldMessenger.of(context)
                  .showSnackBar(SnackBar(content: Text(t.lockedSnack)))
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
                if (recommended && !completed) ...[
                  Chip(
                    label: Text(t.recommendedBadge),
                    avatar: const Icon(Icons.star, size: 14),
                    visualDensity: VisualDensity.compact,
                    labelStyle: const TextStyle(fontSize: 11),
                  ),
                  const SizedBox(height: 4),
                ] else if (node.unlockedByScore && !completed) ...[
                  Chip(
                    label: Text(t.unlockedByScoreBadge),
                    avatar: const Icon(Icons.bolt, size: 14),
                    visualDensity: VisualDensity.compact,
                    labelStyle: const TextStyle(fontSize: 11),
                  ),
                  const SizedBox(height: 4),
                ],
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
                    t.nodeMeta(
                        axisLabels(t)[node.skillAxis] ?? node.skillAxis,
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

/// Düğüm detayı: video + AI ödev görevi + ödev yükleme
class NodeDetailScreen extends StatefulWidget {
  final SkillNode node;
  const NodeDetailScreen({super.key, required this.node});

  @override
  State<NodeDetailScreen> createState() => _NodeDetailScreenState();
}

class _NodeDetailScreenState extends State<NodeDetailScreen> {
  bool _submitting = false;
  bool _completedNow = false;
  String? _assignment;
  bool _assignmentBusy = false;

  @override
  void initState() {
    super.initState();
    _loadAssignment();
  }

  Future<void> _loadAssignment() async {
    // Kayıtlı ödev varsa gösterilir — bu çağrı AI kotası harcamaz
    try {
      final text = await ApiClient.instance.getAssignment(widget.node.id);
      if (mounted && text != null) setState(() => _assignment = text);
    } catch (_) {/* sessiz — bölüm butonla kalır */}
  }

  Future<void> _generateAssignment() async {
    setState(() => _assignmentBusy = true);
    // Burada sayfa geçişi yok, o yüzden finally güvenli.
    AiWait.show(context, title: AppLocalizations.of(context).aiWaitTitleAssignment);
    try {
      final text = await ApiClient.instance.generateAssignment(widget.node.id);
      if (mounted) setState(() => _assignment = text);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(friendlyError(context, e))));
      }
    } finally {
      if (mounted) {
        AiWait.hide(context);
        setState(() => _assignmentBusy = false);
      }
    }
  }

  Future<void> _submit(ImageSource source) async {
    // Seçiciyi açmadan ÖNCE işaretle: Android kamera/galeri sırasında Artora'yı
    // öldürebiliyor, o durumda dönüşte bu bayrak sayesinde fotoğrafı kurtarıyoruz.
    await PendingAnalysis.mark(widget.node.id, PendingAnalysis.stagePicking);
    final file = await ImagePicker().pickImage(source: source, maxWidth: 1600);
    // Seçici async gap; dönüşte ekran hâlâ ayakta mı (bkz. _freeAnalysis)
    if (file == null || !mounted) {
      await PendingAnalysis.clear(); // kullanıcı vazgeçti
      return;
    }
    await _sendAssignment(file);
  }

  /// Dosya elde edildikten sonraki kısım — kurtarma akışı da buraya giriyor.
  Future<void> _sendAssignment(XFile file) async {
    if (!mounted) return;
    setState(() => _submitting = true);
    await PendingAnalysis.clear(); // seçim tamam, takibi iş kimliği devralıyor
    if (!mounted) return;

    int jobId;
    try {
      jobId = await ApiClient.instance
          .submitAssignmentAsync(widget.node.id, await file.readAsBytes(), file.name);
    } catch (e) {
      if (!mounted) return;
      setState(() => _submitting = false);
      showErrorWithStoreAction(context, e); // 402'de "Jeton Al" kısayolu
      return;
    }
    await AnalysisWatcher.remember(jobId);
    if (!mounted) return;

    // Yükleme bitti; analiz artık SUNUCUDA koşuyor. Kullanıcı çıksa da iş
    // kaybolmaz — bekleme modalı bu yüzden artık veri kaybını önleyen bir
    // güvenlik önlemi değil, yalnızca daha iyi bir deneyim.
    AiWait.show(context);
    AnalysisJobInfo? job;
    Object? error;
    try {
      job = await AnalysisWatcher.waitFor(jobId);
    } catch (e) {
      error = e;
    }
    if (!mounted) return;
    AiWait.hide(context);
    setState(() => _submitting = false);

    final t = AppLocalizations.of(context);
    if (error != null) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(friendlyError(context, error))));
      return;
    }
    final done = job!;
    if (done.status == 'failed') {
      // Sunucu jetonu iade etti; mesaj yerelleştirilmiş olarak oradan geliyor
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(done.error ?? t.errorUnexpected)));
      return;
    }
    final analysis = done.analysis;
    if (done.status != 'done' || analysis == null) {
      // İstemci zaman aşımı — iş sunucuda sürüyor, sonuç kaybolmuyor
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(t.analysisStillRunning),
          duration: const Duration(seconds: 6)));
      return;
    }
    if (done.xpAwarded > 0) _completedNow = true;
    await Navigator.of(context).push(MaterialPageRoute(
      builder: (_) => RedlineScreen(
        image: FileImage(File(file.path)),
        analysis: analysis,
        xpAwarded: done.xpAwarded,
        submissionId: done.submissionId,
      ),
    ));
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
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
                  title: Text(t.videoSoon),
                  subtitle: Text(t.videoSoonBody),
                ),
              )
            else
              for (final r in node.resources)
                Card(
                  child: ListTile(
                    leading: Icon(
                        r.isPlaylist ? Icons.playlist_play : Icons.play_circle),
                    title: Text(r.title),
                    subtitle: Text(t.resourceMeta(
                        r.author,
                        r.isPlaylist
                            ? t.resourceKindPlaylist
                            : t.resourceKindVideo)),
                    trailing: const Icon(Icons.open_in_new, size: 18),
                    onTap: () => launchUrl(r.url),
                  ),
                ),
            const SizedBox(height: 16),
            // AI ödev görevi (müşteri isteği: "ödevi yapay zeka verecek")
            Text(t.assignmentSection,
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            if (_assignment != null)
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Text(_assignment!),
                ),
              )
            else if (_assignmentBusy)
              const Center(child: CircularProgressIndicator())
            else
              OutlinedButton.icon(
                icon: const Icon(Icons.auto_awesome),
                label: Text(t.assignmentGenerate),
                onPressed: _generateAssignment,
              ),
            const SizedBox(height: 16),
            Text(t.uploadHomework,
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            Text(t.uploadHint),
            const SizedBox(height: 16),
            if (_submitting)
              const Center(child: CircularProgressIndicator())
            else ...[
              FilledButton.icon(
                icon: const Icon(Icons.folder),
                label: Text(t.submitFromDevice),
                onPressed: () => _submit(ImageSource.gallery),
              ),
              const SizedBox(height: 8),
              OutlinedButton.icon(
                icon: const Icon(Icons.camera_alt),
                label: Text(t.submitFromCamera),
                onPressed: () => _submit(ImageSource.camera),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
