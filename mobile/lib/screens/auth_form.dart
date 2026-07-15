import 'package:flutter/material.dart';

import '../api.dart';
import '../google_auth.dart';
import 'home_shell.dart';
import 'onboarding.dart';

enum AuthMode { login, register, upgrade }

/// Tek form, üç mod: giriş / kayıt / misafir hesabını yükseltme.
class AuthFormScreen extends StatefulWidget {
  final AuthMode mode;
  const AuthFormScreen({super.key, required this.mode});

  @override
  State<AuthFormScreen> createState() => _AuthFormScreenState();
}

class _AuthFormScreenState extends State<AuthFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _email = TextEditingController();
  final _password = TextEditingController();
  final _name = TextEditingController();
  bool _busy = false;

  String get _title => switch (widget.mode) {
        AuthMode.login => 'Giriş Yap',
        AuthMode.register => 'Kayıt Ol',
        AuthMode.upgrade => 'Hesap Oluştur',
      };

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _busy = true);
    final api = ApiClient.instance;
    try {
      switch (widget.mode) {
        case AuthMode.login:
          await api.login(_email.text.trim(), _password.text);
        case AuthMode.register:
          await api.register(_email.text.trim(), _password.text,
              _name.text.trim().isEmpty ? 'Çizer' : _name.text.trim());
        case AuthMode.upgrade:
          await api.upgradeGuest(_email.text.trim(), _password.text);
      }
      if (!mounted) return;
      switch (widget.mode) {
        case AuthMode.login:
          // Var olan hesap: onboarding'i zaten yaptıysa doğrudan ana ekran
          Navigator.of(context).pushAndRemoveUntil(
              MaterialPageRoute(builder: (_) => const HomeShell()), (_) => false);
        case AuthMode.register:
          Navigator.of(context).pushAndRemoveUntil(
              MaterialPageRoute(builder: (_) => const PickImagesScreen()),
              (_) => false);
        case AuthMode.upgrade:
          Navigator.of(context).pop(true);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(friendlyError(e))));
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _google() async {
    if (widget.mode != AuthMode.upgrade) {
      return signInWithGoogleAndRoute(context);
    }
    // Yükseltme: mevcut misafir token'ıyla çağır, ilerleme korunur
    setState(() => _busy = true);
    try {
      final idToken = await getGoogleIdToken();
      if (idToken == null) return;
      await ApiClient.instance.googleLogin(idToken);
      if (mounted) Navigator.of(context).pop(true);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(friendlyError(e))));
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(_title)),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Form(
          key: _formKey,
          child: Column(
            children: [
              if (widget.mode == AuthMode.upgrade)
                const Padding(
                  padding: EdgeInsets.only(bottom: 16),
                  child: Text('İlerlemen aynen korunacak — sadece e-posta ve '
                      'şifre ekliyoruz ki hesabın güvende olsun.'),
                ),
              if (widget.mode == AuthMode.register)
                TextFormField(
                  controller: _name,
                  decoration: const InputDecoration(labelText: 'Görünen ad'),
                ),
              TextFormField(
                controller: _email,
                keyboardType: TextInputType.emailAddress,
                decoration: const InputDecoration(labelText: 'E-posta'),
                validator: (v) =>
                    v != null && v.contains('@') ? null : 'Geçerli bir e-posta gir',
              ),
              TextFormField(
                controller: _password,
                obscureText: true,
                decoration: const InputDecoration(labelText: 'Şifre'),
                validator: (v) =>
                    v != null && v.length >= 8 ? null : 'En az 8 karakter',
              ),
              const SizedBox(height: 24),
              _busy
                  ? const CircularProgressIndicator()
                  : FilledButton(onPressed: _submit, child: Text(_title)),
              const SizedBox(height: 16),
              const Row(children: [
                Expanded(child: Divider()),
                Padding(
                  padding: EdgeInsets.symmetric(horizontal: 8),
                  child: Text('veya'),
                ),
                Expanded(child: Divider()),
              ]),
              const SizedBox(height: 16),
              OutlinedButton.icon(
                icon: const Icon(Icons.g_mobiledata, size: 28),
                label: const Text('Google ile Devam Et'),
                onPressed: _busy ? null : _google,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
