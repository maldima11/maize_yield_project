// List all saved records with sync status badges, delete, manual sync button

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import '../database/field_database.dart';
import '../services/sync_service.dart';

class RecordsScreen extends StatefulWidget {
  const RecordsScreen({super.key});

  @override
  State<RecordsScreen> createState() => _RecordsScreenState();
}

class _RecordsScreenState extends State<RecordsScreen> {
  List<FieldRecord> _records = [];
  bool _loading = true;
  bool _isSyncing = false;

  @override
  void initState() {
    super.initState();
    _loadRecords();
  }

  Future<void> _loadRecords() async {
    setState(() => _loading = true);
    final records = await FieldDatabase.instance.getAllRecords();
    setState(() {
      _records = records;
      _loading = false;
    });
  }

  Future<void> _syncAll() async {
    final online = await SyncService.isOnline();
    if (!online) {
      _showSnack('No internet connection. Please connect and try again.');
      return;
    }
    setState(() => _isSyncing = true);
    final result = await SyncService.runBackgroundSync();
    setState(() => _isSyncing = false);
    _showSnack(result.message);
    await _loadRecords();
  }

  Future<void> _deleteRecord(int id) async {
    await FieldDatabase.instance.deleteRecord(id);
    await _loadRecords();
  }

  void _showSnack(String msg) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(msg),
        backgroundColor: const Color(0xFF2E7D32),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F0E8),
      appBar: AppBar(
        title: const Text('📋 Field Records'),
        actions: [
          if (_records.any((r) => !r.isSynced))
            Padding(
              padding: const EdgeInsets.only(right: 8),
              child: TextButton.icon(
                onPressed: _isSyncing ? null : _syncAll,
                icon: _isSyncing
                    ? const SizedBox(
                        width: 14,
                        height: 14,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : const Icon(Icons.sync, color: Colors.white, size: 18),
                label: Text(
                  _isSyncing ? 'Syncing...' : 'Sync All',
                  style: const TextStyle(color: Colors.white, fontSize: 13),
                ),
              ),
            ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadRecords,
            tooltip: 'Refresh',
          ),
        ],
      ),
      body: _loading
          ? const Center(
              child: CircularProgressIndicator(color: Color(0xFF2E7D32)),
            )
          : _records.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Text('🌱', style: TextStyle(fontSize: 48)),
                      const SizedBox(height: 12),
                      Text(
                        'No records yet',
                        style: GoogleFonts.playfairDisplay(
                          fontSize: 18,
                          fontWeight: FontWeight.w700,
                          color: const Color(0xFF0D2B0F),
                        ),
                      ),
                      const SizedBox(height: 6),
                      const Text(
                        'Go to New Entry to log your first field visit',
                        style: TextStyle(color: Color(0xFF888888), fontSize: 13),
                      ),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _loadRecords,
                  color: const Color(0xFF2E7D32),
                  child: ListView.separated(
                    padding: const EdgeInsets.all(16),
                    itemCount: _records.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 10),
                    itemBuilder: (context, i) {
                      final r = _records[i];
                      return _RecordCard(
                        record: r,
                        onDelete: () => showDialog(
                          context: context,
                          builder: (_) => AlertDialog(
                            title: const Text('Delete Record?'),
                            content: const Text(
                              'This will permanently delete this field record.',
                            ),
                            actions: [
                              TextButton(
                                onPressed: () => Navigator.pop(context),
                                child: const Text('Cancel'),
                              ),
                              ElevatedButton(
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: Colors.red,
                                ),
                                onPressed: () {
                                  Navigator.pop(context);
                                  _deleteRecord(r.id!);
                                },
                                child: const Text('Delete'),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ),
    );
  }
}

// ── Record card ──────────────────────────────────────────────────────────────
class _RecordCard extends StatelessWidget {
  final FieldRecord record;
  final VoidCallback onDelete;

  const _RecordCard({required this.record, required this.onDelete});

  @override
  Widget build(BuildContext context) {
    final date = DateTime.tryParse(record.createdAt);
    final formatted = date != null
        ? DateFormat('dd MMM yyyy · HH:mm').format(date)
        : record.createdAt;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border(
          left: BorderSide(
            color: record.isSynced
                ? const Color(0xFF4CAF50)
                : const Color(0xFFF9A825),
            width: 4,
          ),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header row
          Row(
            children: [
              Expanded(
                child: Text(
                  '${record.district} — ${record.ward}',
                  style: const TextStyle(
                    fontWeight: FontWeight.w700,
                    fontSize: 15,
                    color: Color(0xFF0D2B0F),
                  ),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: record.isSynced
                      ? const Color(0xFFE8F5E9)
                      : const Color(0xFFFFF8E1),
                  borderRadius: BorderRadius.circular(999),
                ),
                child: Text(
                  record.isSynced ? '✅ Synced' : '⏳ Pending',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                    color: record.isSynced
                        ? const Color(0xFF2E7D32)
                        : const Color(0xFFF9A825),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              GestureDetector(
                onTap: onDelete,
                child: const Icon(Icons.delete_outline,
                    color: Color(0xFFCCCCCC), size: 20),
              ),
            ],
          ),
          const SizedBox(height: 8),

          // Data row
          Wrap(
            spacing: 12,
            runSpacing: 6,
            children: [
              _Chip(Icons.grass_outlined, record.variety),
              _Chip(Icons.water_drop_outlined, '${record.soilMoisture}% moisture'),
              _Chip(Icons.thermostat_outlined, 'pH ${record.phLevel}'),
              _Chip(Icons.science_outlined, '${record.fertilizerKgPerHa} kg/ha'),
              _Chip(Icons.gps_fixed, '${record.latitude.toStringAsFixed(4)}, ${record.longitude.toStringAsFixed(4)}'),
            ],
          ),

          const SizedBox(height: 8),
          Text(
            'Logged: $formatted  ·  Farmer: ${record.officerName}',
            style: const TextStyle(fontSize: 11, color: Color(0xFF888888)),
          ),

          if (record.notes.isNotEmpty) ...[
            const SizedBox(height: 6),
            Text(
              '📝 ${record.notes}',
              style: const TextStyle(fontSize: 12, color: Color(0xFF555555)),
            ),
          ],
        ],
      ),
    );
  }
}

class _Chip extends StatelessWidget {
  final IconData icon;
  final String label;
  const _Chip(this.icon, this.label);

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 13, color: const Color(0xFF2E7D32)),
        const SizedBox(width: 4),
        Text(label, style: const TextStyle(fontSize: 12, color: Color(0xFF444444))),
      ],
    );
  }
}