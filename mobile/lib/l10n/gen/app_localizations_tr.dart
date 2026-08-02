// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Turkish (`tr`).
class AppLocalizationsTr extends AppLocalizations {
  AppLocalizationsTr([String locale = 'tr']) : super(locale);

  @override
  String get tabMentors => 'Mentorlar';

  @override
  String get tabLessons => 'Dersler';

  @override
  String get tabGallery => 'Topluluk';

  @override
  String get tabProfile => 'Profil';

  @override
  String get galleryEmpty =>
      'Henüz paylaşılan çizim yok. Gelişim Macerası\'ndaki anahtarla kendi çizimini herkese açabilirsin!';

  @override
  String get reportButton => 'Bildir';

  @override
  String get reportSheetTitle => 'Bu çizimi neden bildiriyorsun?';

  @override
  String get reportReasonUygunsuz => 'Uygunsuz içerik';

  @override
  String get reportReasonSpam => 'Spam / alakasız';

  @override
  String get reportReasonTelif => 'Telif ihlali';

  @override
  String get reportReasonDiger => 'Diğer';

  @override
  String get reportThanks => 'Bildirimin alındı, inceleyeceğiz. Teşekkürler!';

  @override
  String get adminTabApplications => 'Başvurular';

  @override
  String get adminTabReports => 'Şikayetler';

  @override
  String get adminNoReports => 'Bekleyen şikayet yok.';

  @override
  String adminReportCount(int count, String reasons) {
    return '$count şikayet: $reasons';
  }

  @override
  String get adminHide => 'Kaldır';

  @override
  String get adminDismiss => 'Sorun Yok';

  @override
  String get welcomeTagline => 'Çizimde gelişim yolculuğun burada başlıyor.';

  @override
  String get continueAsGuest => 'Misafir Olarak Devam Et';

  @override
  String get continueWithGoogle => 'Google ile Devam Et';

  @override
  String get signIn => 'Giriş Yap';

  @override
  String get signUp => 'Kayıt Ol';

  @override
  String get createAccount => 'Hesap Oluştur';

  @override
  String get guestDefaultName => 'Misafir Çizer';

  @override
  String get artistDefaultName => 'Çizer';

  @override
  String get errorNetwork =>
      'Sunucuya ulaşılamadı. İnternet bağlantını ve backend\'i kontrol et.';

  @override
  String get errorUnexpected => 'Beklenmeyen bir sorun oluştu.';

  @override
  String get upgradeNote =>
      'İlerlemen aynen korunacak — sadece e-posta ve şifre ekliyoruz ki hesabın güvende olsun.';

  @override
  String get labelDisplayName => 'Görünen ad';

  @override
  String get labelEmail => 'E-posta';

  @override
  String get labelPassword => 'Şifre';

  @override
  String get validEmail => 'Geçerli bir e-posta gir';

  @override
  String get validPasswordMin => 'En az 8 karakter';

  @override
  String get orDivider => 'veya';

  @override
  String get pickTitle => 'Son 3 Çizimini Yükle';

  @override
  String get pickIntro =>
      'Seviyeni belirlemek için son yaptığın 3 çizimi seç. Mükemmel olmaları gerekmiyor — olduğun yerden başlıyoruz.';

  @override
  String pickContinue(int count) {
    return 'Devam Et ($count/3)';
  }

  @override
  String get pickCamera => 'Kamera ile çek';

  @override
  String get pickGallery => 'Cihazdan seç';

  @override
  String get skip => 'Atla';

  @override
  String get chartEmptyCta => 'Seviye belirlemeyi başlat';

  @override
  String get analyzingTitle => 'Resimlerin inceleniyor...';

  @override
  String get analyzingSubtitle => 'Bu birkaç saniye sürebilir.';

  @override
  String analyzeRetry(String error) {
    return '$error Birazdan tekrar denenecek.';
  }

  @override
  String get resultTitle => 'Değerlendirme Sonucu';

  @override
  String levelHeading(int level) {
    return '$level. Seviye';
  }

  @override
  String scoreDetermined(int score) {
    return '$score/100 — belirlendi';
  }

  @override
  String get goToTree => 'Yetenek Ağacına Git';

  @override
  String get mentorsComingTitle => 'Mentor pazarı çok yakında!';

  @override
  String get mentorsComingBody =>
      'Şimdilik her ödevine anında ücretsiz AI analizi alabilirsin. Gerçek mentorlar bir sonraki sürümde burada olacak.';

  @override
  String treeLoadError(String error) {
    return 'Ağaç yüklenemedi: $error';
  }

  @override
  String get lockedSnack =>
      'Bu ders için önce önceki dersleri tamamlaman gerekiyor.';

  @override
  String nodeMeta(String axis, int xp) {
    return '$axis • $xp XP';
  }

  @override
  String get videoSoon => 'Video yakında';

  @override
  String get videoSoonBody => 'Bu dersin içeriği henüz eklenmedi.';

  @override
  String get resourceKindPlaylist => 'Oynatma listesi';

  @override
  String get resourceKindVideo => 'Video';

  @override
  String resourceMeta(String author, String kind) {
    return '$author • $kind';
  }

  @override
  String get recommendedBadge => 'Önerilen';

  @override
  String get unlockedByScoreBadge => 'Skorunla açıldı';

  @override
  String get ownCourseNote =>
      'Bu sıra bir öneri — kendi kursun veya kaynağın varsa aynı konuyu oradan çalışıp ödevini yine buraya yükleyebilirsin.';

  @override
  String get assignmentSection => 'Ödevin';

  @override
  String get assignmentGenerate => 'AI\'dan ödev al';

  @override
  String get freeAnalysisTitle => 'Serbest Analiz';

  @override
  String get freeAnalysisHint =>
      'Ders dışı bitmiş bir çizimini yükle, AI teknik analiz yapsın (haftada 1 ücretsiz).';

  @override
  String get levelRoadmapTitle => 'Seviye Yol Haritası';

  @override
  String levelRoadmapEntry(int level, int xp) {
    return '$level. Seviye — $xp XP';
  }

  @override
  String get levelRoadmapCurrent => 'Buradasın';

  @override
  String get uploadHomework => 'Ödevini yükle';

  @override
  String get uploadHint =>
      'Videoyu izledikten sonra çalışmanı yükle; saniyeler içinde yapıcı bir redline analizi alacaksın.';

  @override
  String get submitFromDevice => 'Cihazdan Seç ve Gönder';

  @override
  String get submitFromCamera => 'Kamera ile Çek ve Gönder';

  @override
  String get aiAnalysisTitle => 'AI Analizi';

  @override
  String xpGained(int xp) {
    return '+$xp XP kazandın!';
  }

  @override
  String get strengthsTitle => 'Güçlü yönlerin';

  @override
  String get findingsTitle => 'Gelişim noktaları';

  @override
  String suggestionPrefix(String text) {
    return 'Öneri: $text';
  }

  @override
  String profileLoadError(String error) {
    return 'Profil yüklenemedi: $error';
  }

  @override
  String get createAccountCard => 'Hesap oluştur';

  @override
  String get createAccountCardBody =>
      'İlerlemen cihaz silinse bile güvende kalsın.';

  @override
  String levelBadge(int level, int xp) {
    return '$level. Seviye • $xp XP';
  }

  @override
  String get abilityChartTitle => 'Ability Chart';

  @override
  String get abilityChartHint =>
      'Bir eksene dokunarak ilgili derslere gidebilirsin.';

  @override
  String get chartEmpty =>
      'Seviye belirleme tamamlanınca chart burada görünecek.';

  @override
  String scoreOutOf(int score) {
    return '$score/100';
  }

  @override
  String get journeyTitle => 'Gelişim Macerası';

  @override
  String get journeyHint => 'Yüklediğin ödevler ve AI notların, kronolojik.';

  @override
  String get journeyEmpty =>
      'İlk ödevini yüklediğinde maceran burada başlayacak!';

  @override
  String get homeworkFallback => 'Ödev';

  @override
  String get privacyKeyHint =>
      'Anahtar: açık = herkese görünür, kapalı = sadece sen (varsayılan).';

  @override
  String get languageTitle => 'Dil / Language';

  @override
  String get languageTurkish => 'Türkçe';

  @override
  String get languageEnglish => 'English';

  @override
  String get darkModeTitle => 'Karanlık Tema';

  @override
  String get darkModeSubtitle => 'Uygulamayı koyu renklerle kullan';

  @override
  String get feedbackButton => 'Geri bildirim gönder';

  @override
  String get sendFeedbackBody =>
      'Beta\'da bir sorun mu gördün, fikrin mi var? Bize yaz!';

  @override
  String get feedbackMailSubject => 'Artora Beta geri bildirimi';

  @override
  String feedbackMailBody(String version) {
    return 'Merhaba! Artora hakkında geri bildirimim:\n\n\n---\nSürüm: $version';
  }

  @override
  String get signOut => 'Çıkış Yap';

  @override
  String get signOutConfirmTitle => 'Çıkış yapılsın mı?';

  @override
  String get signOutConfirmBody =>
      'Aynı hesapla tekrar giriş yapabilirsin; ilerlemen sunucuda güvende.';

  @override
  String get signOutGuestBody =>
      'Misafir hesabına tekrar GİRİLEMEZ — ilerlemen kaybolur. Kaybetmemek için önce profilden hesap oluştur.';

  @override
  String get deleteAccount => 'Hesabı Sil';

  @override
  String get deleteAccountBody => 'Hesabın ve tüm çizimlerin kalıcı silinir.';

  @override
  String get deleteConfirmTitle => 'Hesabı sil?';

  @override
  String get deleteConfirmBody =>
      'Hesabın, ilerlemen ve yüklediğin tüm çizimler kalıcı olarak silinecek. Bu işlem geri alınamaz.';

  @override
  String get cancel => 'Vazgeç';

  @override
  String get continueButton => 'Devam Et';

  @override
  String get deleteConfirm2Title => 'Emin misin?';

  @override
  String get deleteConfirm2Body => 'Son onay: tüm verilerin şimdi silinecek.';

  @override
  String get deleteFinalButton => 'Hesabımı Kalıcı Olarak Sil';

  @override
  String get mentorsEmpty =>
      'Henüz onaylı mentor yok — ilk mentor sen olabilirsin!';

  @override
  String get mentorStyleAll => 'Tümü';

  @override
  String mentorAnsweredCount(int count) {
    return '$count cevap';
  }

  @override
  String get mentorPortfolioTitle => 'Portfolyo';

  @override
  String get mentorAsk => 'Havuza sor — 1 jeton';

  @override
  String mentorAskSent(String name) {
    return 'Ödevin $name adlı mentora iletildi!';
  }

  @override
  String jetonBalance(int count) {
    return '$count ücretsiz jeton';
  }

  @override
  String goldJetonBalance(int count) {
    return '$count altın jeton';
  }

  @override
  String get becomeMentor => 'Mentor Ol';

  @override
  String get becomeMentorBody =>
      'Deneyimini paylaş, öğrencilerin ödevlerine geri bildirim ver.';

  @override
  String get mentorApplyTitle => 'Mentor Başvurusu';

  @override
  String get mentorBioLabel => 'Kısa biyografi';

  @override
  String get mentorStylesLabel => 'Uzman olduğun stiller';

  @override
  String get mentorPortfolioPick =>
      'Galerinden örnek eser seç (herkese açık olur)';

  @override
  String get mentorApplySubmit => 'Başvuruyu Gönder';

  @override
  String get mentorApplyPending => 'Mentor başvurun inceleniyor.';

  @override
  String get mentorApplyRejected =>
      'Başvurun onaylanmadı — güncelleyip tekrar başvurabilirsin.';

  @override
  String get mentorPanelTitle => 'Mentor Paneli';

  @override
  String get mentorAvailableSwitch => 'Yeni istek almaya açığım';

  @override
  String get mentorQueueEmpty =>
      'Şu an bekleyen istek yok — biri ödev gönderince burada görünecek.';

  @override
  String get mentorFeedbackTitle => 'Mentor geri bildirimi';

  @override
  String get writeFeedback => 'Geri bildirim yaz';

  @override
  String get feedbackHint =>
      'Yapıcı ol: önce güçlü yönler, sonra somut öneriler.';

  @override
  String get sendFeedback => 'Gönder';

  @override
  String get myRequestsTitle => 'Mentor İsteklerim';

  @override
  String get requestStatusAssigned => 'Mentor inceliyor';

  @override
  String get requestStatusAnswered => 'Cevaplandı';

  @override
  String get requestStatusExpired => 'Süresi doldu — jetonun iade edildi';

  @override
  String get rateFeedback => 'Puanla';

  @override
  String get ratedThanks => 'Teşekkürler, puanın kaydedildi!';

  @override
  String get mentorSearchHint => 'Mentor ara (ad veya bio)...';

  @override
  String get mentorAskDirect => 'Soru sor — 3 jeton';

  @override
  String get mentorAskDirectGold => 'Soru sor — 3 altın jeton';

  @override
  String get mentorGoldRequestHint =>
      'Altın (öncelikli) istek — detaylı geri bildirim beklenir';

  @override
  String get mentorPickDrawing => 'Hangi çizimini göndereceksin?';

  @override
  String get mentorNoDrawings =>
      'Önce bir ders ödevini yüklemen gerekiyor — analiz sonrası buradan mentora gönderebilirsin.';

  @override
  String get jetonPaymentTitle => 'Ödeme nasıl işler?';

  @override
  String get mentorPoolPaymentInfo =>
      'Havuz isteği 1 jeton. Önce ücretsiz jetonların harcanır; ücretsiz jetonun kalmadıysa altın jetondan düşülür. İsteğin havuzdaki rastgele müsait bir mentora gider.';

  @override
  String get mentorDirectPaymentInfo =>
      'Seçmeli mentorluk 3 altın jeton. Yalnız satın alınan altın jetonlar geçerlidir — ücretsiz (haftalık hediye) jetonlar burada kullanılamaz. Bunun nedeni, ödemenin bir kısmının doğrudan seçtiğin mentora gitmesi; bu yüzden gerçek bir ödemeden gelmesi gerekir.';

  @override
  String get mentorEarningsTitle => 'Kazancım';

  @override
  String mentorEarningsUnit(int count) {
    return '$count jeton-eşdeğeri';
  }

  @override
  String mentorEarningsAnswered(int count) {
    return '$count cevaplanan istek';
  }

  @override
  String get mentorEarningsSoon =>
      'Ödeme altyapısı yakında — kazançların şimdiden birikiyor.';

  @override
  String get storeTitle => 'Altın Jeton Mağazası';

  @override
  String get storeGoldExplainer =>
      'Altın jetonlar gerçek satın alımdır. Seçmeli (öncelikli) mentorluk için gereklidir ve mentorlara ödenen kazancın kaynağıdır. Havuz mentoru + AI analizi için her hafta hediye edilen ücretsiz jetonlar yeter; altın jetonu yalnız seçmeli mentorluk veya ekstra ücretsiz jeton istersen al.';

  @override
  String get storeJetonSection => 'Altın jeton paketleri';

  @override
  String storeJetonPack(int count) {
    return '$count altın jeton';
  }

  @override
  String get storePremiumTitle => 'Artora Premium';

  @override
  String storePremiumPerk1(int count) {
    return 'Her ay $count altın jeton hediye';
  }

  @override
  String get storePremiumPerk2 => 'Günlük AI analiz limitin 5 katına çıkar';

  @override
  String get storePremiumPerk3 =>
      'Dersler zaten herkese ücretsiz — Premium sadece hız katar';

  @override
  String storePremiumActive(String date) {
    return 'Premium aktif — $date tarihine kadar';
  }

  @override
  String get storeSubscribe => 'Abone Ol';

  @override
  String get storeBuy => 'Satın Al';

  @override
  String get storeRestore => 'Satın alımları geri yükle';

  @override
  String get storeUnavailable =>
      'Mağaza şu an kullanılamıyor (Play Store bağlantısı yok).';

  @override
  String storeSuccess(int count) {
    return 'Satın alma tamamlandı — güncel altın jeton bakiyen: $count';
  }

  @override
  String get storeBuyJetons => 'Altın Jeton Al';

  @override
  String get premiumBadge => 'Premium';

  @override
  String get adminPanelTitle => 'Admin — Mentor Başvuruları';

  @override
  String get adminSectionTitle => 'Admin Paneli';

  @override
  String get adminSectionBody =>
      'Bekleyen mentor başvurularını incele ve onayla.';

  @override
  String get adminNoApplications => 'Bekleyen başvuru yok.';

  @override
  String get adminApprove => 'Onayla';

  @override
  String get adminReject => 'Reddet';

  @override
  String adminDecided(String name, String decision) {
    return '$name: $decision';
  }

  @override
  String get adminDecisionApproved => 'onaylandı';

  @override
  String get adminDecisionRejected => 'reddedildi';

  @override
  String get styleManga => 'Manga';

  @override
  String get styleRealist => 'Realist';

  @override
  String get styleKarikatur => 'Karikatür';

  @override
  String get styleAnime => 'Anime';

  @override
  String get styleDijital => 'Dijital';

  @override
  String get styleKarakalem => 'Karakalem';

  @override
  String get axisAnatomi => 'Anatomi';

  @override
  String get axisPerspektif => 'Perspektif';

  @override
  String get axisIsikGolge => 'Işık-Gölge';

  @override
  String get axisOran => 'Oran';

  @override
  String get axisCizgiKalitesi => 'Çizgi Kalitesi';

  @override
  String get axisKompozisyon => 'Kompozisyon';

  @override
  String get axisRenk => 'Renk';
}
