import 'package:flutter/material.dart';

import '../api.dart';
import '../l10n/gen/app_localizations.dart';
import 'redline.dart';

/// Faz 2: onaylı mentorun paneli — müsaitlik anahtarı + atanmış istek kuyruğu.
/// İstek detayında öğrencinin çizimi + AI analizi görülür, metin geri bildirim yazılır.
class MentorPanelScreen extends StatefulWidget {
  /// null = bilinmiyor (bildirim derin bağlantısından açıldı) — profilden çekilir.
  final bool? initialAvailable;
  const MentorPanelScreen({super.key, this.initialAvailable});

  @override
  State<MentorPanelScreen> createState() => _MentorPanelScreenState();
}

class _MentorPanelScreenState extends State<MentorPanelScreen> {
  late Future<List<MentorQueueItem>> _future;
  late Future<EarningsInfo> _earnings;
  late bool _available;

  @override
  void initState() {
    super.initState();
    _available = widget.initialAvailable ?? true;
    if (widget.initialAvailable == null) {
      // Derin bağlantıyla gelindi: gerçek müsaitlik profilden okunur
      ApiClient.instance.getProfile().then((p) {
        final mentor = p['mentor'] as Map<String, dynamic>?;
        if (mounted && mentor != null) {
          setState(() => _available = mentor['is_available'] == true);
        }
      }).catchError((_) {});
    }
    _future = ApiClient.instance.getMentorQueue();
    _earnings = ApiClient.instance.getMentorEarnings();
  }

  void _reload() => setState(() {
        _future = ApiClient.instance.getMentorQueue();
        _earnings = ApiClient.instance.getMentorEarnings(); // cevap sonrası tazele
      });

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(t.mentorPanelTitle)),
      body: Column(
        children: [
          SwitchListTile(
            title: Text(t.mentorAvailableSwitch),
            value: _available,
            onChanged: (v) async {
              setState(() => _available = v);
              try {
                await ApiClient.instance.setMentorAvailability(v);
              } catch (e) {
                if (context.mounted) {
                  setState(() => _available = !v);
                  ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text(friendlyError(context, e))));
                }
              }
            },
          ),
          _EarningsCard(future: _earnings),
          const Divider(height: 1),
          Expanded(
            child: FutureBuilder(
              future: _future,
              builder: (context, snapshot) {
                if (snapshot.hasError) {
                  return Center(
                      child: Text(friendlyError(context, snapshot.error!)));
                }
                if (!snapshot.hasData) {
                  return const Center(child: CircularProgressIndicator());
                }
                final items = snapshot.data!;
                if (items.isEmpty) {
                  return Center(
                    child: Padding(
                      padding: const EdgeInsets.all(32),
                      child:
                          Text(t.mentorQueueEmpty, textAlign: TextAlign.center),
                    ),
                  );
                }
                return RefreshIndicator(
                  onRefresh: () async => _reload(),
                  child: ListView(
                    padding: const EdgeInsets.all(12),
                    children: [
                      for (final item in items)
                        Card(
                          child: ListTile(
                            leading: ClipRRect(
                              borderRadius: BorderRadius.circular(6),
                              child: Image.network(
                                ApiClient.instance.imageUrl(item.submissionId),
                                headers: ApiClient.instance.authHeaders,
                                width: 48,
                                height: 48,
                                fit: BoxFit.cover,
                                errorBuilder: (_, _, _) =>
                                    const Icon(Icons.image),
                              ),
                            ),
                            title: Row(children: [
                              Flexible(child: Text(item.studentDisplayName)),
                              if (item.gold) ...[
                                const SizedBox(width: 6),
                                Tooltip(
                                  message: AppLocalizations.of(context)
                                      .mentorGoldRequestHint,
                                  child: const Icon(Icons.paid,
                                      size: 16, color: Color(0xFFD4AF37)),
                                ),
                              ],
                            ]),
                            subtitle: Text(item.nodeId ?? ''),
                            trailing: item.status == 'answered'
                                ? const Icon(Icons.check_circle,
                                    color: Colors.green)
                                : const Icon(Icons.pending_outlined),
                            onTap: () async {
                              final answered = await Navigator.of(context)
                                  .push<bool>(MaterialPageRoute(
                                      builder: (_) =>
                                          _RequestDetailScreen(item: item)));
                              if (answered == true) _reload();
                            },
                          ),
                        ),
                    ],
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

/// Faz 4 (gelir paylaşımı): mentorun birikmiş kazancı (jeton-eşdeğeri) +
/// "ödemeler yakında" notu. Kazanç okunamıyorsa (hata) sessizce gizlenir —
/// panelin ana işlevi (kuyruk) etkilenmez.
class _EarningsCard extends StatelessWidget {
  final Future<EarningsInfo> future;
  const _EarningsCard({required this.future});

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final scheme = Theme.of(context).colorScheme;
    return FutureBuilder<EarningsInfo>(
      future: future,
      builder: (context, snapshot) {
        if (!snapshot.hasData) return const SizedBox.shrink();
        final e = snapshot.data!;
        return Card(
          margin: const EdgeInsets.fromLTRB(12, 12, 12, 4),
          color: scheme.primaryContainer,
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Icon(Icons.savings_outlined, color: scheme.onPrimaryContainer),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(t.mentorEarningsTitle,
                          style: Theme.of(context).textTheme.labelLarge?.copyWith(
                              color: scheme.onPrimaryContainer)),
                      const SizedBox(height: 2),
                      Text(
                        t.mentorEarningsUnit(e.jetonEquivalent),
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                            color: scheme.onPrimaryContainer,
                            fontWeight: FontWeight.bold),
                      ),
                      Text(
                        t.mentorEarningsAnswered(e.answeredCount),
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: scheme.onPrimaryContainer),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        t.mentorEarningsSoon,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: scheme.onPrimaryContainer,
                            fontStyle: FontStyle.italic),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _RequestDetailScreen extends StatefulWidget {
  final MentorQueueItem item;
  const _RequestDetailScreen({required this.item});

  @override
  State<_RequestDetailScreen> createState() => _RequestDetailScreenState();
}

class _RequestDetailScreenState extends State<_RequestDetailScreen> {
  final _controller = TextEditingController();
  bool _busy = false;

  Future<void> _send() async {
    if (_controller.text.trim().isEmpty) return;
    setState(() => _busy = true);
    try {
      await ApiClient.instance
          .sendMentorFeedback(widget.item.id, _controller.text.trim());
      if (mounted) Navigator.of(context).pop(true);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(friendlyError(context, e))));
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final item = widget.item;
    return Scaffold(
      appBar: AppBar(title: Text(item.studentDisplayName)),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Öğrencinin çizimi, varsa AI bulgu işaretleriyle (mentora bağlam verir)
          if (item.aiResult != null)
            AspectRatio(
              aspectRatio: 3 / 4,
              child: RedlineImage(
                image: NetworkImage(
                  ApiClient.instance.imageUrl(item.submissionId),
                  headers: ApiClient.instance.authHeaders,
                ),
                analysis: item.aiResult!,
              ),
            )
          else
            Image.network(
              ApiClient.instance.imageUrl(item.submissionId),
              headers: ApiClient.instance.authHeaders,
              errorBuilder: (_, _, _) => const Icon(Icons.image, size: 64),
            ),
          const SizedBox(height: 16),
          if (item.status == 'answered')
            Card(
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Row(children: [
                  const Icon(Icons.check_circle, color: Colors.green),
                  const SizedBox(width: 8),
                  Text(t.requestStatusAnswered),
                ]),
              ),
            )
          else ...[
            Text(t.writeFeedback,
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            TextField(
              controller: _controller,
              maxLines: 6,
              decoration: InputDecoration(
                hintText: t.feedbackHint,
                border: const OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            _busy
                ? const Center(child: CircularProgressIndicator())
                : FilledButton.icon(
                    icon: const Icon(Icons.send),
                    label: Text(t.sendFeedback),
                    onPressed: _send,
                  ),
          ],
        ],
      ),
    );
  }
}
