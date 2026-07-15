import 'package:google_sign_in/google_sign_in.dart';

/// Backend'in token doğrulamada kullandığı web/server OAuth client ID'si.
/// Build: flutter run --dart-define=GOOGLE_SERVER_CLIENT_ID=xxx.apps.googleusercontent.com
const _serverClientId = String.fromEnvironment('GOOGLE_SERVER_CLIENT_ID');

bool _initialized = false;

/// Google hesabıyla oturum açar ve backend'e verilecek ID token'ı döner.
/// Kullanıcı akıştan vazgeçerse null döner.
Future<String?> getGoogleIdToken() async {
  if (_serverClientId.isEmpty) {
    throw StateError(
        'Google girişi bu build\'de yapılandırılmamış (GOOGLE_SERVER_CLIENT_ID yok).');
  }
  final signIn = GoogleSignIn.instance;
  if (!_initialized) {
    await signIn.initialize(serverClientId: _serverClientId);
    _initialized = true;
  }
  try {
    final account = await signIn.authenticate();
    return account.authentication.idToken;
  } on GoogleSignInException catch (e) {
    if (e.code == GoogleSignInExceptionCode.canceled) return null;
    rethrow;
  }
}
