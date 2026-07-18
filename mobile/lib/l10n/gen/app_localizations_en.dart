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
  String get tabProfile => 'Profile';

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
  String get mentorAsk => 'Ask a mentor — 1 jeton';

  @override
  String mentorAskSent(String name) {
    return 'Your assignment was sent to mentor $name!';
  }

  @override
  String jetonBalance(int count) {
    return '$count jetons';
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
  String get rateFeedback => 'Rate';

  @override
  String get ratedThanks => 'Thanks, your rating was saved!';

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
