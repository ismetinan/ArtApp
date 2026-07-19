import 'package:flutter/material.dart';

import '../api.dart';
import '../l10n/gen/app_localizations.dart';

/// Beta admin paneli: bekleyen mentor başvurularını listeler, onayla/reddet.
/// Sadece is_admin hesaplarda profil ekranından erişilir.
class AdminPanelScreen extends StatefulWidget {
  const AdminPanelScreen({super.key});

  @override
  State<AdminPanelScreen> createState() => _AdminPanelScreenState();
}

class _AdminPanelScreenState extends State<AdminPanelScreen> {
  late Future<List<Map<String, dynamic>>> _future;

  @override
  void initState() {
    super.initState();
    _future = ApiClient.instance.getMentorApplications();
  }

  void _refresh() {
    setState(() => _future = ApiClient.instance.getMentorApplications());
  }

  Future<void> _decide(Map<String, dynamic> app, bool approve) async {
    final t = AppLocalizations.of(context);
    try {
      await ApiClient.instance
          .decideMentorApplication(app['id'] as int, approve);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(t.adminDecided(
              app['display_name'] as String? ?? '?',
              approve ? t.adminDecisionApproved : t.adminDecisionRejected))));
      _refresh();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(friendlyError(context, e))));
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final styles = styleLabels(t);
    return Scaffold(
      appBar: AppBar(title: Text(t.adminPanelTitle)),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: _future,
        builder: (context, snap) {
          if (snap.hasError) {
            return Center(child: Text(friendlyError(context, snap.error!)));
          }
          if (!snap.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          final apps = snap.data!;
          if (apps.isEmpty) {
            return Center(child: Text(t.adminNoApplications));
          }
          return RefreshIndicator(
            onRefresh: () async => _refresh(),
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: apps.length,
              itemBuilder: (context, i) {
                final app = apps[i];
                final portfolio =
                    List<int>.from(app['portfolio_submission_ids'] ?? []);
                final appStyles = List<String>.from(app['styles'] ?? []);
                return Card(
                  margin: const EdgeInsets.only(bottom: 16),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(app['display_name'] as String? ?? '?',
                            style: Theme.of(context).textTheme.titleMedium),
                        if ((app['bio'] as String? ?? '').isNotEmpty) ...[
                          const SizedBox(height: 8),
                          Text(app['bio'] as String),
                        ],
                        if (appStyles.isNotEmpty) ...[
                          const SizedBox(height: 8),
                          Wrap(
                            spacing: 8,
                            children: [
                              for (final s in appStyles)
                                Chip(
                                    label: Text(styles[s] ?? s),
                                    visualDensity: VisualDensity.compact),
                            ],
                          ),
                        ],
                        if (portfolio.isNotEmpty) ...[
                          const SizedBox(height: 12),
                          SizedBox(
                            height: 96,
                            child: ListView.separated(
                              scrollDirection: Axis.horizontal,
                              itemCount: portfolio.length,
                              separatorBuilder: (_, _) =>
                                  const SizedBox(width: 8),
                              itemBuilder: (context, j) => ClipRRect(
                                borderRadius: BorderRadius.circular(8),
                                child: Image.network(
                                  ApiClient.instance.imageUrl(portfolio[j]),
                                  headers: ApiClient.instance.authHeaders,
                                  width: 96,
                                  height: 96,
                                  fit: BoxFit.cover,
                                  errorBuilder: (_, _, _) => const SizedBox(
                                      width: 96,
                                      child:
                                          Icon(Icons.broken_image_outlined)),
                                ),
                              ),
                            ),
                          ),
                        ],
                        const SizedBox(height: 12),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.end,
                          children: [
                            OutlinedButton(
                              onPressed: () => _decide(app, false),
                              child: Text(t.adminReject),
                            ),
                            const SizedBox(width: 8),
                            FilledButton(
                              onPressed: () => _decide(app, true),
                              child: Text(t.adminApprove),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          );
        },
      ),
    );
  }
}
