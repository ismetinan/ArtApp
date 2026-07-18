import 'package:flutter/material.dart';

import '../api.dart';
import '../l10n/gen/app_localizations.dart';

/// Mentorlar sekmesi (CLAUDE.md §7.5): stil filtresi + mentor kartları.
/// mentor_market_enabled kapalıysa Faz 1 placeholder'ı gösterilir.
class MentorsScreen extends StatefulWidget {
  const MentorsScreen({super.key});

  @override
  State<MentorsScreen> createState() => _MentorsScreenState();
}

class _MentorsScreenState extends State<MentorsScreen> {
  Future<List<MentorInfo>>? _future;
  String? _style;

  @override
  void initState() {
    super.initState();
    if (ApiClient.instance.mentorMarketEnabled) _load();
  }

  void _load() =>
      setState(() => _future = ApiClient.instance.getMentors(style: _style));

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    if (!ApiClient.instance.mentorMarketEnabled) {
      return Scaffold(
        appBar: AppBar(title: Text(t.tabMentors)),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.people_outline, size: 64),
                const SizedBox(height: 16),
                Text(t.mentorsComingTitle,
                    style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: 8),
                Text(t.mentorsComingBody, textAlign: TextAlign.center),
              ],
            ),
          ),
        ),
      );
    }

    final styles = styleLabels(t);
    return Scaffold(
      appBar: AppBar(title: Text(t.tabMentors)),
      body: Column(
        children: [
          SizedBox(
            height: 56,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              children: [
                Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: FilterChip(
                    label: Text(t.mentorStyleAll),
                    selected: _style == null,
                    onSelected: (_) {
                      _style = null;
                      _load();
                    },
                  ),
                ),
                for (final e in styles.entries)
                  Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: FilterChip(
                      label: Text(e.value),
                      selected: _style == e.key,
                      onSelected: (_) {
                        _style = e.key;
                        _load();
                      },
                    ),
                  ),
              ],
            ),
          ),
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
                final mentors = snapshot.data!;
                if (mentors.isEmpty) {
                  return Center(
                    child: Padding(
                      padding: const EdgeInsets.all(32),
                      child: Text(t.mentorsEmpty, textAlign: TextAlign.center),
                    ),
                  );
                }
                return RefreshIndicator(
                  onRefresh: () async => _load(),
                  child: ListView(
                    padding: const EdgeInsets.all(12),
                    children: [
                      for (final m in mentors) _MentorCard(mentor: m),
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

class _MentorCard extends StatelessWidget {
  final MentorInfo mentor;
  const _MentorCard({required this.mentor});

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final styles = styleLabels(t);
    return Card(
      child: ListTile(
        leading: mentor.portfolioSubmissionIds.isEmpty
            ? const CircleAvatar(child: Icon(Icons.person))
            : ClipRRect(
                borderRadius: BorderRadius.circular(6),
                child: Image.network(
                  ApiClient.instance.imageUrl(mentor.portfolioSubmissionIds.first),
                  headers: ApiClient.instance.authHeaders,
                  width: 48,
                  height: 48,
                  fit: BoxFit.cover,
                  errorBuilder: (_, _, _) => const Icon(Icons.image),
                ),
              ),
        title: Text(mentor.displayName),
        subtitle: Text(
          [
            if (mentor.styles.isNotEmpty)
              mentor.styles.map((s) => styles[s] ?? s).join(', '),
            if (mentor.bio.isNotEmpty) mentor.bio,
          ].join(' • '),
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
        ),
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            if (mentor.rating != null)
              Row(mainAxisSize: MainAxisSize.min, children: [
                const Icon(Icons.star, size: 16, color: Colors.amber),
                Text(' ${mentor.rating!.toStringAsFixed(1)}'),
              ]),
            Text(t.mentorAnsweredCount(mentor.answeredCount),
                style: Theme.of(context).textTheme.bodySmall),
          ],
        ),
        onTap: () => Navigator.of(context).push(
          MaterialPageRoute(builder: (_) => MentorProfileScreen(mentor: mentor)),
        ),
      ),
    );
  }
}

/// Mentor profili (CLAUDE.md §7.6): ad, stiller, bio, portfolyo galerisi.
class MentorProfileScreen extends StatelessWidget {
  final MentorInfo mentor;
  const MentorProfileScreen({super.key, required this.mentor});

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final styles = styleLabels(t);
    return Scaffold(
      appBar: AppBar(title: Text(mentor.displayName)),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Row(children: [
            const CircleAvatar(radius: 32, child: Icon(Icons.person, size: 32)),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(mentor.displayName,
                      style: Theme.of(context).textTheme.titleLarge),
                  if (mentor.rating != null)
                    Row(children: [
                      const Icon(Icons.star, size: 16, color: Colors.amber),
                      Text(
                          ' ${mentor.rating!.toStringAsFixed(1)} • ${t.mentorAnsweredCount(mentor.answeredCount)}'),
                    ]),
                ],
              ),
            ),
          ]),
          const SizedBox(height: 12),
          if (mentor.styles.isNotEmpty)
            Wrap(
              spacing: 8,
              children: [
                for (final s in mentor.styles) Chip(label: Text(styles[s] ?? s)),
              ],
            ),
          if (mentor.bio.isNotEmpty) ...[
            const SizedBox(height: 12),
            Text(mentor.bio),
          ],
          const SizedBox(height: 16),
          Text(t.mentorPortfolioTitle,
              style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          GridView.count(
            crossAxisCount: 3,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            mainAxisSpacing: 8,
            crossAxisSpacing: 8,
            children: [
              for (final sid in mentor.portfolioSubmissionIds)
                ClipRRect(
                  borderRadius: BorderRadius.circular(8),
                  child: Image.network(
                    ApiClient.instance.imageUrl(sid),
                    headers: ApiClient.instance.authHeaders,
                    fit: BoxFit.cover,
                    errorBuilder: (_, _, _) => const Icon(Icons.image),
                  ),
                ),
            ],
          ),
        ],
      ),
    );
  }
}
