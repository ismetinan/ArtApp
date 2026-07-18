import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_tr.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'gen/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('tr'),
  ];

  /// No description provided for @tabMentors.
  ///
  /// In tr, this message translates to:
  /// **'Mentorlar'**
  String get tabMentors;

  /// No description provided for @tabLessons.
  ///
  /// In tr, this message translates to:
  /// **'Dersler'**
  String get tabLessons;

  /// No description provided for @tabProfile.
  ///
  /// In tr, this message translates to:
  /// **'Profil'**
  String get tabProfile;

  /// No description provided for @welcomeTagline.
  ///
  /// In tr, this message translates to:
  /// **'Çizimde gelişim yolculuğun burada başlıyor.'**
  String get welcomeTagline;

  /// No description provided for @continueAsGuest.
  ///
  /// In tr, this message translates to:
  /// **'Misafir Olarak Devam Et'**
  String get continueAsGuest;

  /// No description provided for @continueWithGoogle.
  ///
  /// In tr, this message translates to:
  /// **'Google ile Devam Et'**
  String get continueWithGoogle;

  /// No description provided for @signIn.
  ///
  /// In tr, this message translates to:
  /// **'Giriş Yap'**
  String get signIn;

  /// No description provided for @signUp.
  ///
  /// In tr, this message translates to:
  /// **'Kayıt Ol'**
  String get signUp;

  /// No description provided for @createAccount.
  ///
  /// In tr, this message translates to:
  /// **'Hesap Oluştur'**
  String get createAccount;

  /// No description provided for @guestDefaultName.
  ///
  /// In tr, this message translates to:
  /// **'Misafir Çizer'**
  String get guestDefaultName;

  /// No description provided for @artistDefaultName.
  ///
  /// In tr, this message translates to:
  /// **'Çizer'**
  String get artistDefaultName;

  /// No description provided for @errorNetwork.
  ///
  /// In tr, this message translates to:
  /// **'Sunucuya ulaşılamadı. İnternet bağlantını ve backend\'i kontrol et.'**
  String get errorNetwork;

  /// No description provided for @errorUnexpected.
  ///
  /// In tr, this message translates to:
  /// **'Beklenmeyen bir sorun oluştu.'**
  String get errorUnexpected;

  /// No description provided for @upgradeNote.
  ///
  /// In tr, this message translates to:
  /// **'İlerlemen aynen korunacak — sadece e-posta ve şifre ekliyoruz ki hesabın güvende olsun.'**
  String get upgradeNote;

  /// No description provided for @labelDisplayName.
  ///
  /// In tr, this message translates to:
  /// **'Görünen ad'**
  String get labelDisplayName;

  /// No description provided for @labelEmail.
  ///
  /// In tr, this message translates to:
  /// **'E-posta'**
  String get labelEmail;

  /// No description provided for @labelPassword.
  ///
  /// In tr, this message translates to:
  /// **'Şifre'**
  String get labelPassword;

  /// No description provided for @validEmail.
  ///
  /// In tr, this message translates to:
  /// **'Geçerli bir e-posta gir'**
  String get validEmail;

  /// No description provided for @validPasswordMin.
  ///
  /// In tr, this message translates to:
  /// **'En az 8 karakter'**
  String get validPasswordMin;

  /// No description provided for @orDivider.
  ///
  /// In tr, this message translates to:
  /// **'veya'**
  String get orDivider;

  /// No description provided for @pickTitle.
  ///
  /// In tr, this message translates to:
  /// **'Son 3 Çizimini Yükle'**
  String get pickTitle;

  /// No description provided for @pickIntro.
  ///
  /// In tr, this message translates to:
  /// **'Seviyeni belirlemek için son yaptığın 3 çizimi seç. Mükemmel olmaları gerekmiyor — olduğun yerden başlıyoruz.'**
  String get pickIntro;

  /// No description provided for @pickContinue.
  ///
  /// In tr, this message translates to:
  /// **'Devam Et ({count}/3)'**
  String pickContinue(int count);

  /// No description provided for @pickCamera.
  ///
  /// In tr, this message translates to:
  /// **'Kamera ile çek'**
  String get pickCamera;

  /// No description provided for @pickGallery.
  ///
  /// In tr, this message translates to:
  /// **'Cihazdan seç'**
  String get pickGallery;

  /// No description provided for @skip.
  ///
  /// In tr, this message translates to:
  /// **'Atla'**
  String get skip;

  /// No description provided for @chartEmptyCta.
  ///
  /// In tr, this message translates to:
  /// **'Seviye belirlemeyi başlat'**
  String get chartEmptyCta;

  /// No description provided for @analyzingTitle.
  ///
  /// In tr, this message translates to:
  /// **'Resimlerin inceleniyor...'**
  String get analyzingTitle;

  /// No description provided for @analyzingSubtitle.
  ///
  /// In tr, this message translates to:
  /// **'Bu birkaç saniye sürebilir.'**
  String get analyzingSubtitle;

  /// No description provided for @analyzeRetry.
  ///
  /// In tr, this message translates to:
  /// **'{error} Birazdan tekrar denenecek.'**
  String analyzeRetry(String error);

  /// No description provided for @resultTitle.
  ///
  /// In tr, this message translates to:
  /// **'Değerlendirme Sonucu'**
  String get resultTitle;

  /// No description provided for @levelHeading.
  ///
  /// In tr, this message translates to:
  /// **'{level}. Seviye'**
  String levelHeading(int level);

  /// No description provided for @scoreDetermined.
  ///
  /// In tr, this message translates to:
  /// **'{score}/100 — belirlendi'**
  String scoreDetermined(int score);

  /// No description provided for @goToTree.
  ///
  /// In tr, this message translates to:
  /// **'Yetenek Ağacına Git'**
  String get goToTree;

  /// No description provided for @mentorsComingTitle.
  ///
  /// In tr, this message translates to:
  /// **'Mentor pazarı çok yakında!'**
  String get mentorsComingTitle;

  /// No description provided for @mentorsComingBody.
  ///
  /// In tr, this message translates to:
  /// **'Şimdilik her ödevine anında ücretsiz AI analizi alabilirsin. Gerçek mentorlar bir sonraki sürümde burada olacak.'**
  String get mentorsComingBody;

  /// No description provided for @treeLoadError.
  ///
  /// In tr, this message translates to:
  /// **'Ağaç yüklenemedi: {error}'**
  String treeLoadError(String error);

  /// No description provided for @lockedSnack.
  ///
  /// In tr, this message translates to:
  /// **'Bu ders için önce önceki dersleri tamamlaman gerekiyor.'**
  String get lockedSnack;

  /// No description provided for @nodeMeta.
  ///
  /// In tr, this message translates to:
  /// **'{axis} • {xp} XP'**
  String nodeMeta(String axis, int xp);

  /// No description provided for @videoSoon.
  ///
  /// In tr, this message translates to:
  /// **'Video yakında'**
  String get videoSoon;

  /// No description provided for @videoSoonBody.
  ///
  /// In tr, this message translates to:
  /// **'Bu dersin içeriği henüz eklenmedi.'**
  String get videoSoonBody;

  /// No description provided for @resourceKindPlaylist.
  ///
  /// In tr, this message translates to:
  /// **'Oynatma listesi'**
  String get resourceKindPlaylist;

  /// No description provided for @resourceKindVideo.
  ///
  /// In tr, this message translates to:
  /// **'Video'**
  String get resourceKindVideo;

  /// No description provided for @resourceMeta.
  ///
  /// In tr, this message translates to:
  /// **'{author} • {kind}'**
  String resourceMeta(String author, String kind);

  /// No description provided for @uploadHomework.
  ///
  /// In tr, this message translates to:
  /// **'Ödevini yükle'**
  String get uploadHomework;

  /// No description provided for @uploadHint.
  ///
  /// In tr, this message translates to:
  /// **'Videoyu izledikten sonra çalışmanı yükle; saniyeler içinde yapıcı bir redline analizi alacaksın.'**
  String get uploadHint;

  /// No description provided for @submitFromDevice.
  ///
  /// In tr, this message translates to:
  /// **'Cihazdan Seç ve Gönder'**
  String get submitFromDevice;

  /// No description provided for @submitFromCamera.
  ///
  /// In tr, this message translates to:
  /// **'Kamera ile Çek ve Gönder'**
  String get submitFromCamera;

  /// No description provided for @aiAnalysisTitle.
  ///
  /// In tr, this message translates to:
  /// **'AI Analizi'**
  String get aiAnalysisTitle;

  /// No description provided for @xpGained.
  ///
  /// In tr, this message translates to:
  /// **'+{xp} XP kazandın!'**
  String xpGained(int xp);

  /// No description provided for @strengthsTitle.
  ///
  /// In tr, this message translates to:
  /// **'Güçlü yönlerin'**
  String get strengthsTitle;

  /// No description provided for @findingsTitle.
  ///
  /// In tr, this message translates to:
  /// **'Gelişim noktaları'**
  String get findingsTitle;

  /// No description provided for @suggestionPrefix.
  ///
  /// In tr, this message translates to:
  /// **'Öneri: {text}'**
  String suggestionPrefix(String text);

  /// No description provided for @profileLoadError.
  ///
  /// In tr, this message translates to:
  /// **'Profil yüklenemedi: {error}'**
  String profileLoadError(String error);

  /// No description provided for @createAccountCard.
  ///
  /// In tr, this message translates to:
  /// **'Hesap oluştur'**
  String get createAccountCard;

  /// No description provided for @createAccountCardBody.
  ///
  /// In tr, this message translates to:
  /// **'İlerlemen cihaz silinse bile güvende kalsın.'**
  String get createAccountCardBody;

  /// No description provided for @levelBadge.
  ///
  /// In tr, this message translates to:
  /// **'{level}. Seviye • {xp} XP'**
  String levelBadge(int level, int xp);

  /// No description provided for @abilityChartTitle.
  ///
  /// In tr, this message translates to:
  /// **'Ability Chart'**
  String get abilityChartTitle;

  /// No description provided for @abilityChartHint.
  ///
  /// In tr, this message translates to:
  /// **'Bir eksene dokunarak ilgili derslere gidebilirsin.'**
  String get abilityChartHint;

  /// No description provided for @chartEmpty.
  ///
  /// In tr, this message translates to:
  /// **'Seviye belirleme tamamlanınca chart burada görünecek.'**
  String get chartEmpty;

  /// No description provided for @scoreOutOf.
  ///
  /// In tr, this message translates to:
  /// **'{score}/100'**
  String scoreOutOf(int score);

  /// No description provided for @journeyTitle.
  ///
  /// In tr, this message translates to:
  /// **'Gelişim Macerası'**
  String get journeyTitle;

  /// No description provided for @journeyHint.
  ///
  /// In tr, this message translates to:
  /// **'Yüklediğin ödevler ve AI notların, kronolojik.'**
  String get journeyHint;

  /// No description provided for @journeyEmpty.
  ///
  /// In tr, this message translates to:
  /// **'İlk ödevini yüklediğinde maceran burada başlayacak!'**
  String get journeyEmpty;

  /// No description provided for @homeworkFallback.
  ///
  /// In tr, this message translates to:
  /// **'Ödev'**
  String get homeworkFallback;

  /// No description provided for @privacyKeyHint.
  ///
  /// In tr, this message translates to:
  /// **'Anahtar: açık = herkese görünür, kapalı = sadece sen (varsayılan).'**
  String get privacyKeyHint;

  /// No description provided for @languageTitle.
  ///
  /// In tr, this message translates to:
  /// **'Dil / Language'**
  String get languageTitle;

  /// No description provided for @languageTurkish.
  ///
  /// In tr, this message translates to:
  /// **'Türkçe'**
  String get languageTurkish;

  /// No description provided for @languageEnglish.
  ///
  /// In tr, this message translates to:
  /// **'English'**
  String get languageEnglish;

  /// No description provided for @deleteAccount.
  ///
  /// In tr, this message translates to:
  /// **'Hesabı Sil'**
  String get deleteAccount;

  /// No description provided for @deleteAccountBody.
  ///
  /// In tr, this message translates to:
  /// **'Hesabın ve tüm çizimlerin kalıcı silinir.'**
  String get deleteAccountBody;

  /// No description provided for @deleteConfirmTitle.
  ///
  /// In tr, this message translates to:
  /// **'Hesabı sil?'**
  String get deleteConfirmTitle;

  /// No description provided for @deleteConfirmBody.
  ///
  /// In tr, this message translates to:
  /// **'Hesabın, ilerlemen ve yüklediğin tüm çizimler kalıcı olarak silinecek. Bu işlem geri alınamaz.'**
  String get deleteConfirmBody;

  /// No description provided for @cancel.
  ///
  /// In tr, this message translates to:
  /// **'Vazgeç'**
  String get cancel;

  /// No description provided for @continueButton.
  ///
  /// In tr, this message translates to:
  /// **'Devam Et'**
  String get continueButton;

  /// No description provided for @deleteConfirm2Title.
  ///
  /// In tr, this message translates to:
  /// **'Emin misin?'**
  String get deleteConfirm2Title;

  /// No description provided for @deleteConfirm2Body.
  ///
  /// In tr, this message translates to:
  /// **'Son onay: tüm verilerin şimdi silinecek.'**
  String get deleteConfirm2Body;

  /// No description provided for @deleteFinalButton.
  ///
  /// In tr, this message translates to:
  /// **'Hesabımı Kalıcı Olarak Sil'**
  String get deleteFinalButton;

  /// No description provided for @mentorsEmpty.
  ///
  /// In tr, this message translates to:
  /// **'Henüz onaylı mentor yok — ilk mentor sen olabilirsin!'**
  String get mentorsEmpty;

  /// No description provided for @mentorStyleAll.
  ///
  /// In tr, this message translates to:
  /// **'Tümü'**
  String get mentorStyleAll;

  /// No description provided for @mentorAnsweredCount.
  ///
  /// In tr, this message translates to:
  /// **'{count} cevap'**
  String mentorAnsweredCount(int count);

  /// No description provided for @mentorPortfolioTitle.
  ///
  /// In tr, this message translates to:
  /// **'Portfolyo'**
  String get mentorPortfolioTitle;

  /// No description provided for @mentorAsk.
  ///
  /// In tr, this message translates to:
  /// **'Mentora sor — 1 jeton'**
  String get mentorAsk;

  /// No description provided for @mentorAskSent.
  ///
  /// In tr, this message translates to:
  /// **'Ödevin {name} adlı mentora iletildi!'**
  String mentorAskSent(String name);

  /// No description provided for @jetonBalance.
  ///
  /// In tr, this message translates to:
  /// **'{count} jeton'**
  String jetonBalance(int count);

  /// No description provided for @becomeMentor.
  ///
  /// In tr, this message translates to:
  /// **'Mentor Ol'**
  String get becomeMentor;

  /// No description provided for @becomeMentorBody.
  ///
  /// In tr, this message translates to:
  /// **'Deneyimini paylaş, öğrencilerin ödevlerine geri bildirim ver.'**
  String get becomeMentorBody;

  /// No description provided for @mentorApplyTitle.
  ///
  /// In tr, this message translates to:
  /// **'Mentor Başvurusu'**
  String get mentorApplyTitle;

  /// No description provided for @mentorBioLabel.
  ///
  /// In tr, this message translates to:
  /// **'Kısa biyografi'**
  String get mentorBioLabel;

  /// No description provided for @mentorStylesLabel.
  ///
  /// In tr, this message translates to:
  /// **'Uzman olduğun stiller'**
  String get mentorStylesLabel;

  /// No description provided for @mentorPortfolioPick.
  ///
  /// In tr, this message translates to:
  /// **'Galerinden örnek eser seç (herkese açık olur)'**
  String get mentorPortfolioPick;

  /// No description provided for @mentorApplySubmit.
  ///
  /// In tr, this message translates to:
  /// **'Başvuruyu Gönder'**
  String get mentorApplySubmit;

  /// No description provided for @mentorApplyPending.
  ///
  /// In tr, this message translates to:
  /// **'Mentor başvurun inceleniyor.'**
  String get mentorApplyPending;

  /// No description provided for @mentorApplyRejected.
  ///
  /// In tr, this message translates to:
  /// **'Başvurun onaylanmadı — güncelleyip tekrar başvurabilirsin.'**
  String get mentorApplyRejected;

  /// No description provided for @mentorPanelTitle.
  ///
  /// In tr, this message translates to:
  /// **'Mentor Paneli'**
  String get mentorPanelTitle;

  /// No description provided for @mentorAvailableSwitch.
  ///
  /// In tr, this message translates to:
  /// **'Yeni istek almaya açığım'**
  String get mentorAvailableSwitch;

  /// No description provided for @mentorQueueEmpty.
  ///
  /// In tr, this message translates to:
  /// **'Şu an bekleyen istek yok — biri ödev gönderince burada görünecek.'**
  String get mentorQueueEmpty;

  /// No description provided for @mentorFeedbackTitle.
  ///
  /// In tr, this message translates to:
  /// **'Mentor geri bildirimi'**
  String get mentorFeedbackTitle;

  /// No description provided for @writeFeedback.
  ///
  /// In tr, this message translates to:
  /// **'Geri bildirim yaz'**
  String get writeFeedback;

  /// No description provided for @feedbackHint.
  ///
  /// In tr, this message translates to:
  /// **'Yapıcı ol: önce güçlü yönler, sonra somut öneriler.'**
  String get feedbackHint;

  /// No description provided for @sendFeedback.
  ///
  /// In tr, this message translates to:
  /// **'Gönder'**
  String get sendFeedback;

  /// No description provided for @myRequestsTitle.
  ///
  /// In tr, this message translates to:
  /// **'Mentor İsteklerim'**
  String get myRequestsTitle;

  /// No description provided for @requestStatusAssigned.
  ///
  /// In tr, this message translates to:
  /// **'Mentor inceliyor'**
  String get requestStatusAssigned;

  /// No description provided for @requestStatusAnswered.
  ///
  /// In tr, this message translates to:
  /// **'Cevaplandı'**
  String get requestStatusAnswered;

  /// No description provided for @requestStatusExpired.
  ///
  /// In tr, this message translates to:
  /// **'Süresi doldu — jetonun iade edildi'**
  String get requestStatusExpired;

  /// No description provided for @rateFeedback.
  ///
  /// In tr, this message translates to:
  /// **'Puanla'**
  String get rateFeedback;

  /// No description provided for @ratedThanks.
  ///
  /// In tr, this message translates to:
  /// **'Teşekkürler, puanın kaydedildi!'**
  String get ratedThanks;

  /// No description provided for @mentorSearchHint.
  ///
  /// In tr, this message translates to:
  /// **'Mentor ara (ad veya bio)...'**
  String get mentorSearchHint;

  /// No description provided for @mentorAskDirect.
  ///
  /// In tr, this message translates to:
  /// **'Soru sor — 3 jeton'**
  String get mentorAskDirect;

  /// No description provided for @mentorPickDrawing.
  ///
  /// In tr, this message translates to:
  /// **'Hangi çizimini göndereceksin?'**
  String get mentorPickDrawing;

  /// No description provided for @mentorNoDrawings.
  ///
  /// In tr, this message translates to:
  /// **'Önce bir ders ödevini yüklemen gerekiyor — analiz sonrası buradan mentora gönderebilirsin.'**
  String get mentorNoDrawings;

  /// No description provided for @styleManga.
  ///
  /// In tr, this message translates to:
  /// **'Manga'**
  String get styleManga;

  /// No description provided for @styleRealist.
  ///
  /// In tr, this message translates to:
  /// **'Realist'**
  String get styleRealist;

  /// No description provided for @styleKarikatur.
  ///
  /// In tr, this message translates to:
  /// **'Karikatür'**
  String get styleKarikatur;

  /// No description provided for @styleAnime.
  ///
  /// In tr, this message translates to:
  /// **'Anime'**
  String get styleAnime;

  /// No description provided for @styleDijital.
  ///
  /// In tr, this message translates to:
  /// **'Dijital'**
  String get styleDijital;

  /// No description provided for @styleKarakalem.
  ///
  /// In tr, this message translates to:
  /// **'Karakalem'**
  String get styleKarakalem;

  /// No description provided for @axisAnatomi.
  ///
  /// In tr, this message translates to:
  /// **'Anatomi'**
  String get axisAnatomi;

  /// No description provided for @axisPerspektif.
  ///
  /// In tr, this message translates to:
  /// **'Perspektif'**
  String get axisPerspektif;

  /// No description provided for @axisIsikGolge.
  ///
  /// In tr, this message translates to:
  /// **'Işık-Gölge'**
  String get axisIsikGolge;

  /// No description provided for @axisOran.
  ///
  /// In tr, this message translates to:
  /// **'Oran'**
  String get axisOran;

  /// No description provided for @axisCizgiKalitesi.
  ///
  /// In tr, this message translates to:
  /// **'Çizgi Kalitesi'**
  String get axisCizgiKalitesi;

  /// No description provided for @axisKompozisyon.
  ///
  /// In tr, this message translates to:
  /// **'Kompozisyon'**
  String get axisKompozisyon;

  /// No description provided for @axisRenk.
  ///
  /// In tr, this message translates to:
  /// **'Renk'**
  String get axisRenk;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en', 'tr'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
    case 'tr':
      return AppLocalizationsTr();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
