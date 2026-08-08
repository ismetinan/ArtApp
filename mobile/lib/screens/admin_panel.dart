import 'package:flutter/material.dart';

import '../api.dart';
import '../l10n/gen/app_localizations.dart';

/// Beta admin paneli: mentor başvuruları + içerik şikayetleri (UGC moderasyonu).
/// Sadece is_admin hesaplarda profil ekranından erişilir.
class AdminPanelScreen extends StatelessWidget {
  const AdminPanelScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: Text(t.adminPanelTitle),
          bottom: TabBar(tabs: [
            Tab(text: t.adminTabApplications),
            Tab(text: t.adminTabReports),
          ]),
        ),
        body: const TabBarView(
          children: [_ApplicationsTab(), _ReportsTab()],
        ),
      ),
    );
  }
}

class _ApplicationsTab extends StatefulWidget {
  const _ApplicationsTab();

  @override
  State<_ApplicationsTab> createState() => _ApplicationsTabState();
}

class _ApplicationsTabState extends State<_ApplicationsTab> {
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

  /// Bağış bağlantısı kararı — başvuru kararından ayrı, listeyi tazeler.
  Future<void> _decideDonation(Map<String, dynamic> app, bool approve) async {
    try {
      await ApiClient.instance.decideDonationLink(app['id'] as int, approve);
      if (mounted) _refresh();
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
    return FutureBuilder<List<Map<String, dynamic>>>(
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
                      // Kalite kapısı: kararın asıl dayanağı bu metin
                      if ((app['sample_critique'] as String? ?? '')
                          .isNotEmpty) ...[
                        const SizedBox(height: 12),
                        Text(t.adminSampleCritique,
                            style: Theme.of(context).textTheme.labelLarge),
                        const SizedBox(height: 4),
                        Text(app['sample_critique'] as String,
                            style: Theme.of(context).textTheme.bodySmall),
                      ],
                      // Bağış bağlantısı AYRI onaylanır: başvuruyu onaylamak
                      // linki onaylamaz (link sonradan da değiştirilebiliyor).
                      if ((app['donation_url'] as String? ?? '')
                          .isNotEmpty) ...[
                        const SizedBox(height: 12),
                        Text(
                            '${t.adminDonationLink} · '
                            '${app['donation_platform'] ?? '?'} · '
                            '${app['donation_status'] ?? '?'}',
                            style: Theme.of(context).textTheme.labelLarge),
                        const SizedBox(height: 4),
                        Text(app['donation_url'] as String,
                            style: Theme.of(context).textTheme.bodySmall),
                        const SizedBox(height: 4),
                        Row(children: [
                          OutlinedButton(
                            onPressed: () => _decideDonation(app, false),
                            child: Text(t.adminRejectLink),
                          ),
                          const SizedBox(width: 8),
                          FilledButton(
                            onPressed: () => _decideDonation(app, true),
                            child: Text(t.adminApproveLink),
                          ),
                        ]),
                      ],
                      if (portfolio.isNotEmpty) ...[
                        const SizedBox(height: 12),
                        SizedBox(
                          height: 96,
                          child: ListView.separated(
                            scrollDirection: Axis.horizontal,
                            itemCount: portfolio.length,
                            separatorBuilder: (_, _) => const SizedBox(width: 8),
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
                                    child: Icon(Icons.broken_image_outlined)),
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
    );
  }
}

/// İçerik şikayetleri: görsel + sahibi + sebepler; Kaldır / Sorun Yok.
class _ReportsTab extends StatefulWidget {
  const _ReportsTab();

  @override
  State<_ReportsTab> createState() => _ReportsTabState();
}

class _ReportsTabState extends State<_ReportsTab> {
  late Future<List<Map<String, dynamic>>> _future;

  @override
  void initState() {
    super.initState();
    _future = ApiClient.instance.getContentReports();
  }

  void _refresh() {
    setState(() => _future = ApiClient.instance.getContentReports());
  }

  Future<void> _decide(int submissionId, bool hide) async {
    try {
      await ApiClient.instance.decideContentReport(submissionId, hide);
      if (mounted) _refresh();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(friendlyError(context, e))));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    return FutureBuilder<List<Map<String, dynamic>>>(
      future: _future,
      builder: (context, snap) {
        if (snap.hasError) {
          return Center(child: Text(friendlyError(context, snap.error!)));
        }
        if (!snap.hasData) {
          return const Center(child: CircularProgressIndicator());
        }
        final reports = snap.data!;
        if (reports.isEmpty) {
          return Center(child: Text(t.adminNoReports));
        }
        return RefreshIndicator(
          onRefresh: () async => _refresh(),
          child: ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: reports.length,
            itemBuilder: (context, i) {
              final r = reports[i];
              final sid = r['submission_id'] as int;
              return Card(
                margin: const EdgeInsets.only(bottom: 16),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      ClipRRect(
                        borderRadius: BorderRadius.circular(8),
                        child: Image.network(
                          ApiClient.instance.imageUrl(sid),
                          headers: ApiClient.instance.authHeaders,
                          height: 180,
                          width: double.infinity,
                          fit: BoxFit.cover,
                          errorBuilder: (_, _, _) =>
                              const Icon(Icons.broken_image_outlined),
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(r['owner_name'] as String? ?? '?',
                          style: Theme.of(context).textTheme.titleMedium),
                      Text(t.adminReportCount(
                          r['report_count'] as int,
                          List<String>.from(r['reasons'] ?? []).join(', '))),
                      const SizedBox(height: 12),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.end,
                        children: [
                          OutlinedButton(
                            onPressed: () => _decide(sid, false),
                            child: Text(t.adminDismiss),
                          ),
                          const SizedBox(width: 8),
                          FilledButton(
                            style: FilledButton.styleFrom(
                                backgroundColor:
                                    Theme.of(context).colorScheme.error),
                            onPressed: () => _decide(sid, true),
                            child: Text(t.adminHide),
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
    );
  }
}
