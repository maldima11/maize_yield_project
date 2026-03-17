import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart'; // kIsWeb
import 'package:google_fonts/google_fonts.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import '../database/field_database.dart';
import '../services/sync_service.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _totalRecords = 0;
  int _unsyncedCount = 0;
  bool _isOnline = true;
  bool _isSyncing = false;
  String _syncMessage = '';

  @override
  void initState() {
    super.initState();
    _loadStats();
    _checkConnectivity();

    // Listen for connectivity changes — skip on web (always online)
    if (!kIsWeb) {
      Connectivity().onConnectivityChanged.listen((result) {
        final online = result != ConnectivityResult.none;
        setState(() => _isOnline = online);
        if (online && _unsyncedCount > 0) {
          _triggerSync();
        }
      });
    }
  }

  Future<void> _loadStats() async {
    // SQLite not available on web — show zeros
    if (kIsWeb) {
      setState(() { _totalRecords = 0; _unsyncedCount = 0; });
      return;
    }
    final all      = await FieldDatabase.instance.getAllRecords();
    final unsynced = await FieldDatabase.instance.countUnsynced();
    setState(() {
      _totalRecords  = all.length;
      _unsyncedCount = unsynced;
    });
  }

  Future<void> _checkConnectivity() async {
    if (kIsWeb) { setState(() => _isOnline = true); return; }
    final online = await SyncService.isOnline();
    setState(() => _isOnline = online);
  }

  Future<void> _triggerSync() async {
    if (_isSyncing || kIsWeb) return;
    setState(() { _isSyncing = true; _syncMessage = 'Syncing...'; });
    final result = await SyncService.runBackgroundSync();
    setState(() { _isSyncing = false; _syncMessage = result.message; });
    await _loadStats();
    Future.delayed(const Duration(seconds: 3), () {
      if (mounted) setState(() => _syncMessage = '');
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F0E8),
      appBar: AppBar(
        title: const Text('🌾 Agritex Field App'),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 16),
            child: Icon(
              _isOnline ? Icons.wifi : Icons.wifi_off,
              color: _isOnline ? const Color(0xFF8BC34A) : Colors.red[300],
            ),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadStats,
        color: const Color(0xFF2E7D32),
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [

              // Welcome banner
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF0D2B0F), Color(0xFF2E7D32)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Good day, Officer 👋',
                      style: GoogleFonts.playfairDisplay(
                        fontSize: 20,
                        fontWeight: FontWeight.w700,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      'Zimbabwe Agritex Digital Support Unit',
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.75),
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 20),

              // Web notice
              if (kIsWeb)
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: const Color(0xFFE3F2FD),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: const Color(0xFF90CAF9)),
                  ),
                  child: const Row(
                    children: [
                      Icon(Icons.info_outline, color: Color(0xFF1565C0), size: 18),
                      SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          'Running in browser preview mode. '
                          'Offline storage and GPS are only available on mobile devices.',
                          style: TextStyle(fontSize: 12, color: Color(0xFF1565C0)),
                        ),
                      ),
                    ],
                  ),
                ),

              if (!kIsWeb) ...[
                // Connectivity status
                AnimatedContainer(
                  duration: const Duration(milliseconds: 300),
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  decoration: BoxDecoration(
                    color: _isOnline
                        ? const Color(0xFFE8F5E9)
                        : const Color(0xFFFFF3E0),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: _isOnline
                          ? const Color(0xFFA5D6A7)
                          : const Color(0xFFFFCC80),
                    ),
                  ),
                  child: Row(
                    children: [
                      Icon(
                        _isOnline ? Icons.cloud_done : Icons.cloud_off,
                        color: _isOnline
                            ? const Color(0xFF2E7D32)
                            : const Color(0xFFE65100),
                        size: 20,
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          _isSyncing
                              ? 'Syncing records to server...'
                              : _syncMessage.isNotEmpty
                                  ? _syncMessage
                                  : _isOnline
                                      ? 'Online — data will sync automatically'
                                      : 'Offline — data saved locally',
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w500,
                            color: _isOnline
                                ? const Color(0xFF1B5E20)
                                : const Color(0xFFE65100),
                          ),
                        ),
                      ),
                      if (_isOnline && _unsyncedCount > 0 && !_isSyncing)
                        TextButton(
                          onPressed: _triggerSync,
                          child: const Text(
                            'Sync Now',
                            style: TextStyle(
                              color: Color(0xFF2E7D32),
                              fontWeight: FontWeight.w700,
                              fontSize: 13,
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
              ],

              const SizedBox(height: 20),

              // KPI cards
              Row(
                children: [
                  _KpiCard(
                    label: 'Total Records',
                    value: kIsWeb ? '--' : '$_totalRecords',
                    icon: Icons.inventory_2_outlined,
                    color: const Color(0xFF2E7D32),
                  ),
                  const SizedBox(width: 12),
                  _KpiCard(
                    label: 'Pending Sync',
                    value: kIsWeb ? '--' : '$_unsyncedCount',
                    icon: Icons.sync_outlined,
                    color: _unsyncedCount > 0
                        ? const Color(0xFFF9A825)
                        : const Color(0xFF2E7D32),
                  ),
                ],
              ),

              const SizedBox(height: 24),

              Text(
                'Quick Actions',
                style: GoogleFonts.playfairDisplay(
                  fontSize: 17,
                  fontWeight: FontWeight.w700,
                  color: const Color(0xFF0D2B0F),
                ),
              ),
              const SizedBox(height: 12),

              _ActionTile(
                icon: Icons.add_location_alt_outlined,
                title: 'Log New Field Visit',
                subtitle: 'Record GPS, soil data & fertilizer',
                onTap: () {},
              ),
              const SizedBox(height: 10),
              _ActionTile(
                icon: Icons.sync,
                title: 'Manual Sync',
                subtitle: kIsWeb
                    ? 'Available on mobile only'
                    : 'Push pending records to server',
                onTap: (!kIsWeb && _isOnline) ? _triggerSync : null,
                disabled: kIsWeb || !_isOnline,
              ),
              const SizedBox(height: 10),
              _ActionTile(
                icon: Icons.bar_chart_outlined,
                title: 'View Regional Trends',
                subtitle: 'Check district performance data',
                onTap: () {},
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ── KPI card ─────────────────────────────────────────────────────────────────
class _KpiCard extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  final Color color;
  const _KpiCard({required this.label, required this.value,
                  required this.icon, required this.color});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(14),
          boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.06),
                                blurRadius: 12, offset: const Offset(0, 4))],
          border: Border(left: BorderSide(color: color, width: 4)),
        ),
        child: Row(
          children: [
            Icon(icon, color: color, size: 28),
            const SizedBox(width: 12),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(value,
                    style: GoogleFonts.playfairDisplay(
                        fontSize: 22, fontWeight: FontWeight.w700,
                        color: const Color(0xFF0D2B0F))),
                Text(label,
                    style: const TextStyle(fontSize: 11, color: Color(0xFF888888))),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

// ── Action tile ──────────────────────────────────────────────────────────────
class _ActionTile extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback? onTap;
  final bool disabled;
  const _ActionTile({required this.icon, required this.title,
                     required this.subtitle, this.onTap, this.disabled = false});

  @override
  Widget build(BuildContext context) {
    return Opacity(
      opacity: disabled ? 0.5 : 1.0,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(14),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(14),
            boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05),
                                  blurRadius: 10, offset: const Offset(0, 3))],
          ),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: const Color(0xFFE8F5E9),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(icon, color: const Color(0xFF2E7D32), size: 22),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: const TextStyle(
                        fontWeight: FontWeight.w600, fontSize: 14,
                        color: Color(0xFF1A1A1A))),
                    Text(subtitle, style: const TextStyle(
                        fontSize: 12, color: Color(0xFF888888))),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right, color: Color(0xFFCCCCCC)),
            ],
          ),
        ),
      ),
    );
  }
}