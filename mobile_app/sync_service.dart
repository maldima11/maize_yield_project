// Connectivity check → fetch unsynced records → POST to Flask → mark synced

import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:connectivity_plus/connectivity_plus.dart';
import '../database/field_database.dart';

class SyncService {
  static const String bgSyncTaskName = 'agritex-field-sync';
  static const String _baseUrl = 'http://YOUR_SERVER_IP:5000'; // Update with your Flask server IP

  // ── Check if device is online ──────────────────────────────────────────────
  static Future<bool> isOnline() async {
    final result = await Connectivity().checkConnectivity();
    return result != ConnectivityResult.none;
  }

  // ── Push a single record to Flask API ─────────────────────────────────────
  static Future<bool> syncRecord(FieldRecord record) async {
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/sync_field_record'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'officer_name': record.officerName,
          'district': record.district,
          'ward': record.ward,
          'variety': record.variety,
          'latitude': record.latitude,
          'longitude': record.longitude,
          'planting_date': record.plantingDate,
          'fertilizer_kg_per_ha': record.fertilizerKgPerHa,
          'soil_moisture': record.soilMoisture,
          'ph_level': record.phLevel,
          'notes': record.notes,
          'created_at': record.createdAt,
        }),
      ).timeout(const Duration(seconds: 10));

      return response.statusCode == 200 || response.statusCode == 201;
    } catch (e) {
      // Network error or timeout — will retry next sync cycle
      return false;
    }
  }

  // ── Main sync function — called manually or by WorkManager ────────────────
  static Future<SyncResult> runBackgroundSync() async {
    // Step 1: Check connectivity
    final online = await isOnline();
    if (!online) {
      return SyncResult(synced: 0, failed: 0, message: 'No internet connection');
    }

    // Step 2: Get all unsynced records from SQLite
    final db = FieldDatabase.instance;
    final unsynced = await db.getUnsyncedRecords();

    if (unsynced.isEmpty) {
      return SyncResult(synced: 0, failed: 0, message: 'All records already synced');
    }

    int synced = 0;
    int failed = 0;

    // Step 3: Push each record to Flask API
    for (final record in unsynced) {
      final success = await syncRecord(record);
      if (success) {
        // Step 4: Mark as synced in local SQLite
        await db.markAsSynced(record.id!);
        synced++;
      } else {
        failed++;
      }
    }

    return SyncResult(
      synced: synced,
      failed: failed,
      message: '$synced record(s) synced, $failed failed',
    );
  }
}

// ── Result model ─────────────────────────────────────────────────────────────
class SyncResult {
  final int synced;
  final int failed;
  final String message;

  const SyncResult({
    required this.synced,
    required this.failed,
    required this.message,
  });
}