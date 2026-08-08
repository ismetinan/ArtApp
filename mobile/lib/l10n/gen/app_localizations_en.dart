// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get tabMentors => 'Mentors';

  @override
  String get tabLessons => 'Lessons';

  @override
  String get tabGallery => 'Community';

  @override
  String get tabProfile => 'Profile';

  @override
  String get galleryEmpty =>
      'No shared drawings yet. Use the switch in your Progress Journey to share your own!';

  @override
  String get reportButton => 'Report';

  @override
  String get reportSheetTitle => 'Why are you reporting this drawing?';

  @override
  String get reportReasonUygunsuz => 'Inappropriate content';

  @override
  String get reportReasonSpam => 'Spam / irrelevant';

  @override
  String get reportReasonTelif => 'Copyright violation';

  @override
  String get reportReasonDiger => 'Other';

  @override
  String get reportThanks => 'Report received, we\'ll review it. Thank you!';

  @override
  String get adminTabApplications => 'Applications';

  @override
  String get adminTabReports => 'Reports';

  @override
  String get adminNoReports => 'No pending reports.';

  @override
  String adminReportCount(int count, String reasons) {
    return '$count report(s): $reasons';
  }

  @override
  String get adminHide => 'Remove';

  @override
  String get adminDismiss => 'Looks Fine';

  @override
  String get welcomeTagline => 'Your journey of growth in drawing starts here.';

  @override
  String get continueAsGuest => 'Continue as Guest';

  @override
  String get continueWithGoogle => 'Continue with Google';

  @override
  String get signIn => 'Sign In';

  @override
  String get signUp => 'Sign Up';

  @override
  String get createAccount => 'Create Account';

  @override
  String get guestDefaultName => 'Guest Artist';

  @override
  String get artistDefaultName => 'Artist';

  @override
  String get errorNetwork =>
      'Couldn\'t reach the server. Check your internet connection.';

  @override
  String get errorUnexpected => 'An unexpected problem occurred.';

  @override
  String get upgradeNote =>
      'Your progress will be kept as-is — we\'re just adding an e-mail and password so your account is safe.';

  @override
  String get labelDisplayName => 'Display name';

  @override
  String get labelEmail => 'E-mail';

  @override
  String get labelPassword => 'Password';

  @override
  String get validEmail => 'Enter a valid e-mail';

  @override
  String get validPasswordMin => 'At least 8 characters';

  @override
  String get orDivider => 'or';

  @override
  String get pickTitle => 'Upload Your Last 3 Drawings';

  @override
  String get pickIntro =>
      'Pick your 3 most recent drawings so we can determine your level. They don\'t need to be perfect — we start from where you are.';

  @override
  String pickContinue(int count) {
    return 'Continue ($count/3)';
  }

  @override
  String get pickCamera => 'Take a photo';

  @override
  String get pickGallery => 'Choose from device';

  @override
  String get skip => 'Skip';

  @override
  String get chartEmptyCta => 'Start the level assessment';

  @override
  String get analyzingTitle => 'Reviewing your drawings...';

  @override
  String get analyzingSubtitle => 'This may take a few seconds.';

  @override
  String analyzeRetry(String error) {
    return '$error Retrying shortly.';
  }

  @override
  String get resultTitle => 'Assessment Result';

  @override
  String levelHeading(int level) {
    return 'Level $level';
  }

  @override
  String scoreDetermined(int score) {
    return '$score/100 — determined';
  }

  @override
  String get goToTree => 'Go to Skill Tree';

  @override
  String get mentorsComingTitle => 'Mentor marketplace coming soon!';

  @override
  String get mentorsComingBody =>
      'For now, you get instant free AI analysis on every assignment. Real mentors will be here in the next release.';

  @override
  String treeLoadError(String error) {
    return 'Couldn\'t load the tree: $error';
  }

  @override
  String get lockedSnack => 'You need to complete the previous lessons first.';

  @override
  String nodeMeta(String axis, int xp) {
    return '$axis • $xp XP';
  }

  @override
  String get videoSoon => 'Video coming soon';

  @override
  String get videoSoonBody => 'This lesson\'s content hasn\'t been added yet.';

  @override
  String get resourceKindPlaylist => 'Playlist';

  @override
  String get resourceKindVideo => 'Video';

  @override
  String resourceMeta(String author, String kind) {
    return '$author • $kind';
  }

  @override
  String get recommendedBadge => 'Recommended';

  @override
  String get unlockedByScoreBadge => 'Unlocked by your score';

  @override
  String get ownCourseNote =>
      'This order is a suggestion — if you follow your own course or resource, study the topic there and upload your assignment here.';

  @override
  String get assignmentSection => 'Your assignment';

  @override
  String get assignmentGenerate => 'Get an assignment from AI';

  @override
  String get freeAnalysisTitle => 'Free Analysis';

  @override
  String get freeAnalysisHint =>
      'Upload a finished drawing outside the lessons and get a technical AI analysis (1 free per week).';

  @override
  String get levelRoadmapTitle => 'Level Roadmap';

  @override
  String levelRoadmapEntry(int level, int xp) {
    return 'Level $level — $xp XP';
  }

  @override
  String get levelRoadmapCurrent => 'You are here';

  @override
  String get uploadHomework => 'Upload your assignment';

  @override
  String get uploadHint =>
      'After watching the video, upload your work; you\'ll get a constructive redline analysis within seconds.';

  @override
  String get submitFromDevice => 'Choose from Device and Send';

  @override
  String get submitFromCamera => 'Take a Photo and Send';

  @override
  String get aiAnalysisTitle => 'AI Analysis';

  @override
  String xpGained(int xp) {
    return 'You earned +$xp XP!';
  }

  @override
  String get strengthsTitle => 'Your strengths';

  @override
  String get findingsTitle => 'Areas to grow';

  @override
  String suggestionPrefix(String text) {
    return 'Suggestion: $text';
  }

  @override
  String profileLoadError(String error) {
    return 'Couldn\'t load profile: $error';
  }

  @override
  String get createAccountCard => 'Create an account';

  @override
  String get createAccountCardBody =>
      'Keep your progress safe even if this device is lost.';

  @override
  String levelBadge(int level, int xp) {
    return 'Level $level • $xp XP';
  }

  @override
  String get abilityChartTitle => 'Ability Chart';

  @override
  String get abilityChartHint => 'Tap an axis to go to its lessons.';

  @override
  String get chartEmpty =>
      'Your chart will appear here after the level assessment.';

  @override
  String scoreOutOf(int score) {
    return '$score/100';
  }

  @override
  String get journeyTitle => 'Progress Journey';

  @override
  String get journeyHint => 'Your uploaded assignments and AI notes, in order.';

  @override
  String get journeyEmpty =>
      'Your journey starts here when you upload your first assignment!';

  @override
  String get homeworkFallback => 'Assignment';

  @override
  String get privacyKeyHint =>
      'Key: on = visible to everyone, off = only you (default).';

  @override
  String get languageTitle => 'Dil / Language';

  @override
  String get languageTurkish => 'Türkçe';

  @override
  String get languageEnglish => 'English';

  @override
  String get darkModeTitle => 'Dark Theme';

  @override
  String get darkModeSubtitle => 'Use the app with dark colors';

  @override
  String get feedbackButton => 'Send feedback';

  @override
  String get sendFeedbackBody =>
      'Found a problem in the beta or have an idea? Tell us!';

  @override
  String get feedbackMailSubject => 'Artora Beta feedback';

  @override
  String feedbackMailBody(String version) {
    return 'Hi! My feedback about Artora:\n\n\n---\nVersion: $version';
  }

  @override
  String get signOut => 'Sign Out';

  @override
  String get signOutConfirmTitle => 'Sign out?';

  @override
  String get signOutConfirmBody =>
      'You can sign back in with the same account; your progress is safe on the server.';

  @override
  String get signOutGuestBody =>
      'A guest account CANNOT be recovered — your progress will be lost. Create an account from your profile first to keep it.';

  @override
  String get deleteAccount => 'Delete Account';

  @override
  String get deleteAccountBody =>
      'Your account and all your drawings are permanently deleted.';

  @override
  String get deleteConfirmTitle => 'Delete account?';

  @override
  String get deleteConfirmBody =>
      'Your account, progress and all uploaded drawings will be permanently deleted. This cannot be undone.';

  @override
  String get cancel => 'Cancel';

  @override
  String get continueButton => 'Continue';

  @override
  String get deleteConfirm2Title => 'Are you sure?';

  @override
  String get deleteConfirm2Body =>
      'Final confirmation: all your data will be deleted now.';

  @override
  String get deleteFinalButton => 'Permanently Delete My Account';

  @override
  String get mentorsEmpty =>
      'No approved mentors yet — you could be the first!';

  @override
  String get mentorStyleAll => 'All';

  @override
  String mentorAnsweredCount(int count) {
    return '$count answers';
  }

  @override
  String get mentorPortfolioTitle => 'Portfolio';

  @override
  String get mentorAsk => 'Ask the pool — 1 jeton';

  @override
  String mentorAskSent(String name) {
    return 'Your assignment was sent to mentor $name!';
  }

  @override
  String jetonBalance(int count) {
    return '$count free jetons';
  }

  @override
  String goldJetonBalance(int count) {
    return '$count gold jetons';
  }

  @override
  String get becomeMentor => 'Become a Mentor';

  @override
  String get becomeMentorBody =>
      'Share your experience and give feedback on students\' assignments.';

  @override
  String get mentorApplyTitle => 'Mentor Application';

  @override
  String get mentorBioLabel => 'Short bio';

  @override
  String get mentorStylesLabel => 'Styles you specialize in';

  @override
  String get mentorPortfolioPick =>
      'Pick sample works from your gallery (they become public)';

  @override
  String get mentorApplySubmit => 'Submit Application';

  @override
  String get mentorApplyPending => 'Your mentor application is under review.';

  @override
  String get mentorApplyRejected =>
      'Your application wasn\'t approved — you can update it and apply again.';

  @override
  String get mentorPanelTitle => 'Mentor Panel';

  @override
  String get mentorAvailableSwitch => 'Open to new requests';

  @override
  String get mentorQueueEmpty =>
      'No pending requests right now — they\'ll appear here when a student sends one.';

  @override
  String get mentorFeedbackTitle => 'Mentor feedback';

  @override
  String get writeFeedback => 'Write feedback';

  @override
  String get feedbackHint =>
      'Be constructive: strengths first, then concrete suggestions.';

  @override
  String get sendFeedback => 'Send';

  @override
  String get myRequestsTitle => 'My Mentor Requests';

  @override
  String get requestStatusAssigned => 'Being reviewed';

  @override
  String get requestStatusAnswered => 'Answered';

  @override
  String get requestStatusExpired => 'Expired — your jeton was refunded';

  @override
  String get requestStatusExpiredFree => 'Expired — you can send it again';

  @override
  String get rateFeedback => 'Rate';

  @override
  String get ratedThanks => 'Thanks, your rating was saved!';

  @override
  String get mentorSearchHint => 'Search mentors (name or bio)...';

  @override
  String get mentorAskDirect => 'Ask this mentor — 3 jetons';

  @override
  String get mentorAskDirectGold => 'Ask this mentor — 3 gold jetons';

  @override
  String get mentorGoldRequestHint =>
      'Gold (priority) request — detailed feedback expected';

  @override
  String get mentorPickDrawing => 'Which drawing do you want to send?';

  @override
  String get mentorNoDrawings =>
      'Upload a lesson assignment first — after the analysis you can send it to a mentor from here.';

  @override
  String shareLevelLockedHint(int level) {
    return 'Sharing to the community unlocks at level $level. For now your drawings stay private to you; as you progress through the lessons you can make them public.';
  }

  @override
  String get jetonPaymentTitle => 'How payment works';

  @override
  String get mentorPoolPaymentInfo =>
      'A pool request costs 1 jeton. Your free jetons are spent first; if you have none left, it comes out of your gold jetons. The request goes to a random available mentor in the pool.';

  @override
  String get mentorDirectPaymentInfo =>
      'Selective mentoring costs 3 gold jetons. Only purchased gold jetons work here — free (weekly gift) jetons can\'t be used. That\'s because part of this payment goes directly to the mentor you picked, so it has to come from a real purchase.';

  @override
  String get mentorEarningsTitle => 'My Earnings';

  @override
  String mentorEarningsUnit(int count) {
    return '$count jeton-equivalent';
  }

  @override
  String mentorEarningsAnswered(int count) {
    return '$count answered requests';
  }

  @override
  String get mentorEarningsSoon =>
      'Payouts coming soon — your earnings are already accruing.';

  @override
  String get jetonAiTitle => 'What is a jeton?';

  @override
  String jetonAiBody(int count, int floor) {
    return 'Every AI analysis costs $count jeton. You get $floor free jetons a week; they don\'t stack — each week your balance is topped back up to $floor. Lesson videos, the skill tree and mentor support are always free.';
  }

  @override
  String jetonWeeklyResetHint(int count) {
    return 'Your free jetons are topped up to $count every week.';
  }

  @override
  String jetonBalanceAi(int count) {
    return '$count jetons';
  }

  @override
  String jetonPurchasedBalance(int count) {
    return '$count purchased';
  }

  @override
  String get mentorFreeTitle => 'Mentor support is free';

  @override
  String mentorFreeInfo(int count) {
    return 'Asking a mentor costs no jetons. To keep it fair: you can ask the same mentor once every 24 hours, and have at most $count open requests at a time.';
  }

  @override
  String get mentorAskFree => 'Ask the pool — free';

  @override
  String get mentorAskDirectFree => 'Ask this mentor — free';

  @override
  String get donationTitle => 'Support this mentor';

  @override
  String get donationBody =>
      'Mentoring is free. If you\'d like, you can support the mentor directly — 100% of what you send goes to them, and Artora takes no cut.';

  @override
  String get donationOptionalNote =>
      'Donations are entirely optional. They unlock nothing in the app, give no one priority, and are not required to receive feedback.';

  @override
  String get donationButton => 'Support';

  @override
  String get donationLeaveTitle => 'Leaving the app';

  @override
  String donationLeaveBody(String platform) {
    return 'You\'ll be taken to $platform. The payment does not go through Artora; Artora is not a party to this transaction and accepts no liability.';
  }

  @override
  String get donationLeaveConfirm => 'Continue';

  @override
  String get mentorRulesTitle => 'Mentor rules';

  @override
  String get mentorRulesBody =>
      '• Feedback is always constructive, never demeaning.\n• Students are assessed within their own style.\n• You may not request payment for feedback; donations are an optional thank-you only.\n• Student drawings may not be shared outside the platform or used for any other purpose.\n• IBAN or card details may not be written in text fields.';

  @override
  String get mentorRulesAccept => 'I have read and accept the mentor rules.';

  @override
  String get mentorSampleCritiqueLabel => 'Sample critique';

  @override
  String mentorSampleCritiqueHint(int count) {
    return 'Pick one of your own drawings and write a constructive, technical critique of it (at least $count characters). We assess your application on this text.';
  }

  @override
  String get mentorDonationLinkLabel => 'Your donation link (optional)';

  @override
  String get mentorDonationLinkHint =>
      'A Kreosus, Shopier, Papara, Patreon, Ko-fi or Buy Me a Coffee link. It appears on your profile once approved.';

  @override
  String get mentorDonationPending => 'Your donation link is awaiting review.';

  @override
  String get mentorDonationApproved =>
      'Your donation link is live on your profile.';

  @override
  String get mentorDonationRejected => 'Your donation link wasn\'t approved.';

  @override
  String get mentorStatsTitle => 'Your reputation';

  @override
  String mentorStatsRating(String rating) {
    return 'Rating: $rating';
  }

  @override
  String get mentorStatsNoRating => 'No rating yet';

  @override
  String get adminSampleCritique => 'Sample critique';

  @override
  String get adminDonationLink => 'Donation link';

  @override
  String get adminApproveLink => 'Approve link';

  @override
  String get adminRejectLink => 'Reject link';

  @override
  String get termsTitle => 'Terms of Service';

  @override
  String get privacyTitle => 'Privacy Policy';

  @override
  String get aiWaitTitle => 'Reviewing your drawing';

  @override
  String get aiWaitTipProportions => 'Assessing proportions and line quality…';

  @override
  String get aiWaitTipPerspective => 'Looking at perspective and anatomy…';

  @override
  String get aiWaitTipLight => 'Examining light and shadow transitions…';

  @override
  String get aiWaitTipComposition => 'Evaluating composition and colour…';

  @override
  String get aiWaitTipWriting => 'Writing your feedback…';

  @override
  String get aiWaitStayHint =>
      'This can take 30-60 seconds. If you leave, the analysis isn\'t lost — it\'s saved to your Progress Journey.';

  @override
  String get recoveredPickRetry =>
      'The photo you picked couldn\'t be sent because the app was closed in the background. Could you open the lesson and try again?';

  @override
  String get analysisStillRunning =>
      'Your analysis is still running. You can close the app — we\'ll notify you when it\'s done.';

  @override
  String get aiWaitTitleAssignment => 'Preparing your assignment';

  @override
  String get aiWaitTitleLevel => 'Determining your level';

  @override
  String storeJetonExplainerAi(int count) {
    return 'Jetons are used for AI analyses. You already get $count free jetons a week and your balance is topped back up to $count every week; jetons you buy here never expire and the weekly top-up doesn\'t touch them. Lessons, the skill tree and mentor support are free — jetons are only for using AI analysis more.';
  }

  @override
  String get storeJetonSectionAi => 'Jeton packs';

  @override
  String storeJetonPackAi(int count) {
    return '$count jetons';
  }

  @override
  String get storePremiumPerkAi1 =>
      'A stronger AI model — more detailed and faster analysis';

  @override
  String storePremiumPerkAi2(int count) {
    return '$count jetons a week';
  }

  @override
  String get storePremiumPerkAi3 =>
      'Lessons and mentor support are already free — Premium boosts the AI side';

  @override
  String get storeTitle => 'Gold Jeton Store';

  @override
  String get storeGoldExplainer =>
      'Gold jetons are a real purchase. They\'re required for selective (priority) mentoring and are the source of the earnings paid out to mentors. The free jetons gifted every week are enough for pool mentoring + AI analysis; only buy gold if you want selective mentoring or extra free jetons.';

  @override
  String get storeJetonSection => 'Gold jeton packs';

  @override
  String storeJetonPack(int count) {
    return '$count gold jetons';
  }

  @override
  String get storePremiumTitle => 'Artora Premium';

  @override
  String storePremiumPerk1(int count) {
    return '$count gold jetons gifted every month';
  }

  @override
  String get storePremiumPerk2 => '5x your daily AI analysis limit';

  @override
  String get storePremiumPerk3 =>
      'Lessons are free for everyone — Premium just adds speed';

  @override
  String storePremiumActive(String date) {
    return 'Premium active — until $date';
  }

  @override
  String get storeSubscribe => 'Subscribe';

  @override
  String get storeBuy => 'Buy';

  @override
  String get storeRestore => 'Restore purchases';

  @override
  String get storeUnavailable =>
      'The store is currently unavailable (no Play Store connection).';

  @override
  String storeSuccess(int count) {
    return 'Purchase complete — your gold jeton balance is now $count';
  }

  @override
  String get storeBuyJetons => 'Buy Gold Jetons';

  @override
  String get premiumBadge => 'Premium';

  @override
  String get adminPanelTitle => 'Admin — Mentor Applications';

  @override
  String get adminSectionTitle => 'Admin Panel';

  @override
  String get adminSectionBody =>
      'Review and approve pending mentor applications.';

  @override
  String get adminNoApplications => 'No pending applications.';

  @override
  String get adminApprove => 'Approve';

  @override
  String get adminReject => 'Reject';

  @override
  String adminDecided(String name, String decision) {
    return '$name: $decision';
  }

  @override
  String get adminDecisionApproved => 'approved';

  @override
  String get adminDecisionRejected => 'rejected';

  @override
  String get styleManga => 'Manga';

  @override
  String get styleRealist => 'Realistic';

  @override
  String get styleKarikatur => 'Cartoon';

  @override
  String get styleAnime => 'Anime';

  @override
  String get styleDijital => 'Digital';

  @override
  String get styleKarakalem => 'Pencil';

  @override
  String get axisAnatomi => 'Anatomy';

  @override
  String get axisPerspektif => 'Perspective';

  @override
  String get axisIsikGolge => 'Light & Shadow';

  @override
  String get axisOran => 'Proportion';

  @override
  String get axisCizgiKalitesi => 'Line Quality';

  @override
  String get axisKompozisyon => 'Composition';

  @override
  String get axisRenk => 'Color';
}
