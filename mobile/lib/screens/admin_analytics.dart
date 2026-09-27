import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../api.dart';
import '../l10n/gen/app_localizations.dart';

/// Admin → Analitik sekmesi. Kullanım görünürlüğü: aktiflik, huni, retention,
/// ders bazlı takılma, ekonomi ve ANONİM kullanıcı listesi. Sunucu kimlik
/// bilgisi (e-posta/ad) döndürmez; burada da yalnız "#id" gösterilir.
/// Grafikler bağımlılık eklememek için CustomPainter ile çiziliyor.
class AdminAnalyticsTab extends StatefulWidget {
  const AdminAnalyticsTab({super.key});

  @override
  State<AdminAnalyticsTab> createState() => _AdminAnalyticsTabState();
}

class _AdminAnalyticsTabState extends State<AdminAnalyticsTab>
    with AutomaticKeepAliveClientMixin {
  static const _sections = ['overview', 'funnel', 'retention', 'lessons', 'economy'];
  late Future<Map<String, Map<String, dynamic>>> _future;

  @override
  bool get wantKeepAlive => true;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<Map<String, Map<String, dynamic>>> _load() async {
    final api = ApiClient.instance;
    final results = await Future.wait(_sections.map(api.getAdminAnalytics));
    return {for (var i = 0; i < _sections.length; i++) _sections[i]: results[i]};
  }

  Future<void> _refresh() async {
    final f = _load();
    setState(() { _future = f; });
    await f;
  }

  @override
  Widget build(BuildContext context) {
    super.build(context);
    final t = AppLocalizations.of(context);
    return FutureBuilder<Map<String, Map<String, dynamic>>>(
      future: _future,
      builder: (context, snap) {
        if (snap.connectionState != ConnectionState.done) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snap.hasError) {
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                Text(friendlyError(context, snap.error!), textAlign: TextAlign.center),
                const SizedBox(height: 12),
                FilledButton(onPressed: _refresh, child: Text(t.analyzeRetryButton)),
              ]),
            ),
          );
        }
        final d = snap.data!;
        return RefreshIndicator(
          onRefresh: _refresh,
          child: ListView(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
            children: [
              _OverviewSection(d['overview']!),
              _FunnelSection(d['funnel']!),
              _RetentionSection(d['retention']!),
              _LessonsSection(d['lessons']!),
              _EconomySection(d['economy']!),
              const SizedBox(height: 8),
              OutlinedButton.icon(
                icon: const Icon(Icons.people_outline),
                label: Text(t.analyticsUsersOpen),
                onPressed: () => Navigator.of(context).push(MaterialPageRoute(
                    builder: (_) => const AdminUsersScreen())),
              ),
            ],
          ),
        );
      },
    );
  }
}

String _pct(num? v) => v == null ? '—' : '%${(v * 100).round()}';

class _SectionTitle extends StatelessWidget {
  final String text;
  const _SectionTitle(this.text);

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(top: 24, bottom: 8),
        child: Text(text, style: Theme.of(context).textTheme.titleMedium),
      );
}

class _Kpi extends StatelessWidget {
  final String label, value;
  const _Kpi(this.label, this.value);

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Container(
      width: 104,
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: cs.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(value,
            style: Theme.of(context)
                .textTheme
                .titleLarge
                ?.copyWith(fontWeight: FontWeight.w600)),
        const SizedBox(height: 2),
        Text(label,
            style: Theme.of(context).textTheme.bodySmall,
            maxLines: 2,
            overflow: TextOverflow.ellipsis),
      ]),
    );
  }
}

// ------------------------------------------------------------------ overview

class _OverviewSection extends StatelessWidget {
  final Map<String, dynamic> d;
  const _OverviewSection(this.d);

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final cs = Theme.of(context).colorScheme;
    final series = (d['series_30d'] as List).cast<Map<String, dynamic>>();
    final platforms = Map<String, dynamic>.from(d['platforms'] as Map);
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(t.analyticsOverview, style: Theme.of(context).textTheme.titleMedium),
      const SizedBox(height: 8),
      Wrap(spacing: 8, runSpacing: 8, children: [
        _Kpi(t.analyticsUsersTotal, '${d['users_total']}'),
        _Kpi(t.analyticsDau, '${d['dau']}'),
        _Kpi(t.analyticsWau, '${d['wau']}'),
        _Kpi(t.analyticsMau, '${d['mau']}'),
        _Kpi(t.analyticsStickiness, _pct(d['stickiness'] as num)),
        _Kpi(t.analyticsNew7d, '${d['new_users_7d']}'),
        _Kpi(t.analyticsRegisteredRate, _pct(d['guest_to_registered_rate'] as num)),
        _Kpi(t.analyticsPremium, '${d['premium_active']}'),
      ]),
      const SizedBox(height: 16),
      Text(t.analyticsLast30d, style: Theme.of(context).textTheme.labelLarge),
      const SizedBox(height: 4),
      SizedBox(
        height: 120,
        width: double.infinity,
        child: CustomPaint(
          painter: _SeriesPainter(
            active: series.map((e) => (e['active'] as num).toInt()).toList(),
            signups: series.map((e) => (e['signups'] as num).toInt()).toList(),
            barColor: cs.primary.withValues(alpha: 0.35),
            lineColor: cs.tertiary,
            gridColor: cs.outlineVariant,
          ),
        ),
      ),
      const SizedBox(height: 4),
      Wrap(spacing: 16, runSpacing: 4, children: [
        _Legend(color: cs.primary.withValues(alpha: 0.35), label: t.analyticsActiveUsers),
        _Legend(color: cs.tertiary, label: t.analyticsSignups),
      ]),
      const SizedBox(height: 12),
      Wrap(
        spacing: 8,
        children: [
          for (final e in platforms.entries)
            Chip(
              visualDensity: VisualDensity.compact,
              label: Text('${e.key}: ${e.value}'),
            ),
        ],
      ),
    ]);
  }
}

class _Legend extends StatelessWidget {
  final Color color;
  final String label;
  const _Legend({required this.color, required this.label});

  @override
  Widget build(BuildContext context) => Row(mainAxisSize: MainAxisSize.min, children: [
        Container(width: 10, height: 10, color: color),
        const SizedBox(width: 4),
        Text(label, style: Theme.of(context).textTheme.bodySmall),
      ]);
}

/// 30 günlük seri: aktif kullanıcı çubukları + kayıt çizgisi (aynı ölçek).
class _SeriesPainter extends CustomPainter {
  final List<int> active, signups;
  final Color barColor, lineColor, gridColor;

  _SeriesPainter({
    required this.active,
    required this.signups,
    required this.barColor,
    required this.lineColor,
    required this.gridColor,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final n = active.length;
    if (n == 0) return;
    final maxV = math.max(1, [...active, ...signups].reduce(math.max));
    final slot = size.width / n;
    final grid = Paint()
      ..color = gridColor
      ..strokeWidth = 1;
    canvas.drawLine(Offset(0, size.height), Offset(size.width, size.height), grid);

    final bar = Paint()..color = barColor;
    for (var i = 0; i < n; i++) {
      final h = size.height * active[i] / maxV;
      canvas.drawRRect(
        RRect.fromRectAndRadius(
          Rect.fromLTWH(i * slot + slot * 0.15, size.height - h, slot * 0.7, h),
          const Radius.circular(2),
        ),
        bar,
      );
    }

    final line = Paint()
      ..color = lineColor
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke;
    final path = Path();
    for (var i = 0; i < n; i++) {
      final p = Offset(i * slot + slot / 2, size.height - size.height * signups[i] / maxV);
      i == 0 ? path.moveTo(p.dx, p.dy) : path.lineTo(p.dx, p.dy);
    }
    canvas.drawPath(path, line);

    // En yüksek değeri sol üstte yaz — ölçek hissi için
    final tp = TextPainter(
      text: TextSpan(text: '$maxV', style: TextStyle(color: gridColor, fontSize: 10)),
      textDirection: TextDirection.ltr,
    )..layout();
    tp.paint(canvas, const Offset(0, 0));
  }

  @override
  bool shouldRepaint(covariant _SeriesPainter old) =>
      old.active != active || old.signups != signups;
}

// -------------------------------------------------------------------- funnel

class _FunnelSection extends StatelessWidget {
  final Map<String, dynamic> d;
  const _FunnelSection(this.d);

  String _label(AppLocalizations t, String key) => switch (key) {
        'signed_up' => t.funnelSignedUp,
        'onboarded' => t.funnelOnboarded,
        'lesson_opened' => t.funnelLessonOpened,
        'assignment_generated' => t.funnelAssignmentGenerated,
        'assignment_submitted' => t.funnelAssignmentSubmitted,
        'lesson_completed' => t.funnelLessonCompleted,
        'returned_after_7d' => t.funnelReturned7d,
        'registered_account' => t.funnelRegistered,
        _ => key,
      };

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final cs = Theme.of(context).colorScheme;
    final steps = (d['steps'] as List).cast<Map<String, dynamic>>();
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      _SectionTitle(t.analyticsFunnel),
      for (final s in steps)
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 4),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              Expanded(child: Text(_label(t, s['key'] as String))),
              Text('${s['users']} · ${_pct(s['rate'] as num)}',
                  style: Theme.of(context).textTheme.bodySmall),
            ]),
            const SizedBox(height: 2),
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: (s['rate'] as num).toDouble().clamp(0, 1),
                minHeight: 8,
                backgroundColor: cs.surfaceContainerHighest,
              ),
            ),
          ]),
        ),
      Padding(
        padding: const EdgeInsets.only(top: 4),
        child: Text(t.analyticsFunnelNote, style: Theme.of(context).textTheme.bodySmall),
      ),
    ]);
  }
}

// ----------------------------------------------------------------- retention

class _RetentionSection extends StatelessWidget {
  final Map<String, dynamic> d;
  const _RetentionSection(this.d);

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final cs = Theme.of(context).colorScheme;
    final cohorts = (d['cohorts'] as List)
        .cast<Map<String, dynamic>>()
        .where((c) => (c['size'] as num) > 0)
        .toList()
        .reversed
        .toList();

    Widget cell(num? v) {
      final bg = v == null
          ? Colors.transparent
          : Color.lerp(cs.surfaceContainerHighest, cs.primary, v.toDouble().clamp(0, 1))!;
      return Container(
        alignment: Alignment.center,
        padding: const EdgeInsets.symmetric(vertical: 6),
        color: bg,
        child: Text(_pct(v),
            style: TextStyle(
                color: v != null && v > 0.5 ? cs.onPrimary : cs.onSurface, fontSize: 12)),
      );
    }

    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      _SectionTitle(t.analyticsRetention),
      if (cohorts.isEmpty)
        Text(t.analyticsNoData)
      else
        Table(
          columnWidths: const {0: FlexColumnWidth(2.2)},
          border: TableBorder.all(color: cs.surface, width: 2),
          children: [
            TableRow(children: [
              Text(t.analyticsCohortWeek, style: Theme.of(context).textTheme.labelSmall),
              for (final h in ['n', 'W1', 'W2', 'W4'])
                Center(child: Text(h, style: Theme.of(context).textTheme.labelSmall)),
            ]),
            for (final c in cohorts)
              TableRow(children: [
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 6),
                  child: Text(c['week_start'] as String,
                      style: const TextStyle(fontSize: 12)),
                ),
                Center(child: Text('${c['size']}', style: const TextStyle(fontSize: 12))),
                cell(c['w1'] as num?),
                cell(c['w2'] as num?),
                cell(c['w4'] as num?),
              ]),
          ],
        ),
      Padding(
        padding: const EdgeInsets.only(top: 4),
        child: Text(t.analyticsRetentionNote, style: Theme.of(context).textTheme.bodySmall),
      ),
    ]);
  }
}

// ------------------------------------------------------------------- lessons

class _LessonsSection extends StatelessWidget {
  final Map<String, dynamic> d;
  const _LessonsSection(this.d);

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final rows = (d['lessons'] as List).cast<Map<String, dynamic>>();
    final small = Theme.of(context).textTheme.bodySmall;
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      _SectionTitle(t.analyticsLessons),
      Text(t.analyticsLessonsLegend, style: small),
      const SizedBox(height: 4),
      for (final r in rows)
        ListTile(
          dense: true,
          contentPadding: EdgeInsets.zero,
          title: Text(r['title'] as String),
          subtitle: Text(
            '👁 ${r['opened']}  📝 ${r['assignment_generated']}  '
            '⬆ ${r['submitters']}  ✅ ${r['completed']}  ⛔ ${r['stuck']}'
            '${r['avg_task_match'] != null ? '  🎯 %${r['avg_task_match']}' : ''}',
            style: small,
          ),
        ),
    ]);
  }
}

// ------------------------------------------------------------------- economy

class _EconomySection extends StatelessWidget {
  final Map<String, dynamic> d;
  const _EconomySection(this.d);

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final jobs = Map<String, dynamic>.from(d['ai_jobs_30d'] as Map);

    Widget kv(String title, Map m) => Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: Theme.of(context).textTheme.labelLarge),
            if (m.isEmpty) Text('—', style: Theme.of(context).textTheme.bodySmall),
            for (final e in m.entries)
              Text('${e.key}: ${e.value}', style: Theme.of(context).textTheme.bodySmall),
            const SizedBox(height: 8),
          ],
        );

    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      _SectionTitle(t.analyticsEconomy),
      kv(t.analyticsJetonsSpent, d['jetons_spent_by_reason'] as Map),
      kv(t.analyticsJetonsGranted, d['jetons_granted_by_reason'] as Map),
      kv(t.analyticsPurchases, d['purchases_by_product'] as Map),
      kv(t.analyticsAiJobs, {
        ...Map<String, dynamic>.from(jobs['by_status'] as Map),
        t.analyticsFailRate: _pct(jobs['fail_rate'] as num),
        t.analyticsAvgSeconds: jobs['avg_seconds'] ?? '—',
      }),
    ]);
  }
}

// --------------------------------------------------------------------- users

/// Anonim kullanıcı listesi — sıralama + sayfalama.
class AdminUsersScreen extends StatefulWidget {
  const AdminUsersScreen({super.key});

  @override
  State<AdminUsersScreen> createState() => _AdminUsersScreenState();
}

class _AdminUsersScreenState extends State<AdminUsersScreen> {
  String _sort = 'last_seen';
  int _page = 0;
  late Future<Map<String, dynamic>> _future;

  @override
  void initState() {
    super.initState();
    _fetch();
  }

  void _fetch() {
    _future = ApiClient.instance
        .getAdminAnalytics('users', {'sort': _sort, 'page': '$_page'});
  }

  String _ago(AppLocalizations t, String? iso) {
    if (iso == null) return '—';
    final diff = DateTime.now().difference(DateTime.parse(iso));
    if (diff.inDays >= 1) return t.analyticsDaysAgo(diff.inDays);
    if (diff.inHours >= 1) return t.analyticsHoursAgo(diff.inHours);
    return t.analyticsJustNow;
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final sorts = {
      'last_seen': t.analyticsSortLastSeen,
      'created': t.analyticsSortCreated,
      'lessons': t.analyticsSortLessons,
      'analyses': t.analyticsSortAnalyses,
      'level': t.analyticsSortLevel,
    };
    return Scaffold(
      appBar: AppBar(
        title: Text(t.analyticsUsersTitle),
        actions: [
          PopupMenuButton<String>(
            icon: const Icon(Icons.sort),
            initialValue: _sort,
            onSelected: (v) => setState(() {
              _sort = v;
              _page = 0;
              _fetch();
            }),
            itemBuilder: (_) => [
              for (final e in sorts.entries)
                PopupMenuItem(value: e.key, child: Text(e.value)),
            ],
          ),
        ],
      ),
      body: FutureBuilder<Map<String, dynamic>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snap.hasError) {
            return Center(child: Text(friendlyError(context, snap.error!)));
          }
          final d = snap.data!;
          final users = (d['users'] as List).cast<Map<String, dynamic>>();
          final total = d['total'] as int;
          final pageSize = d['page_size'] as int;
          final lastPage = ((total - 1) / pageSize).floor();
          final small = Theme.of(context).textTheme.bodySmall;
          return Column(children: [
            Expanded(
              child: ListView.separated(
                itemCount: users.length,
                separatorBuilder: (_, _) => const Divider(height: 1),
                itemBuilder: (_, i) {
                  final u = users[i];
                  final tags = [
                    u['platform'] ?? '?',
                    if (u['app_version'] != null) 'v${u['app_version']}',
                    if (u['is_guest'] == true) t.analyticsGuest,
                    if (u['is_premium'] == true) 'Premium',
                  ].join(' · ');
                  return ListTile(
                    dense: true,
                    title: Text(t.analyticsUserId(u['id'] as int)),
                    subtitle: Text(
                      '$tags\n${t.analyticsUserStats(u['level'] as int, u['lessons_completed'] as int, u['analyses'] as int, u['active_days'] as int)}',
                      style: small,
                    ),
                    isThreeLine: true,
                    trailing: Text(_ago(t, u['last_seen_at'] as String?), style: small),
                  );
                },
              ),
            ),
            if (lastPage > 0)
              SafeArea(
                top: false,
                child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                  IconButton(
                    icon: const Icon(Icons.chevron_left),
                    onPressed: _page == 0
                        ? null
                        : () => setState(() {
                              _page--;
                              _fetch();
                            }),
                  ),
                  Text('${_page + 1} / ${lastPage + 1}'),
                  IconButton(
                    icon: const Icon(Icons.chevron_right),
                    onPressed: _page >= lastPage
                        ? null
                        : () => setState(() {
                              _page++;
                              _fetch();
                            }),
                  ),
                ]),
              ),
          ]);
        },
      ),
    );
  }
}
