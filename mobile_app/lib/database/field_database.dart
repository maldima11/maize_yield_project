// Full SQLite schema, insert, read, mark-synced, delete, count-unsynced

import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';

// ── Data model ───────────────────────────────────────────────────────────────
class FieldRecord {
  final int? id;
  final String officerName;
  final String district;
  final String ward;
  final String variety;
  final double latitude;
  final double longitude;
  final String plantingDate;
  final double fertilizerKgPerHa;
  final double soilMoisture;
  final double phLevel;
  final String notes;
  final String createdAt;
  final bool isSynced;

  const FieldRecord({
    this.id,
    required this.officerName,
    required this.district,
    required this.ward,
    required this.variety,
    required this.latitude,
    required this.longitude,
    required this.plantingDate,
    required this.fertilizerKgPerHa,
    required this.soilMoisture,
    required this.phLevel,
    required this.notes,
    required this.createdAt,
    this.isSynced = false,
  });

  // Convert to map for SQLite insert
  Map<String, dynamic> toMap() => {
        'officer_name': officerName,
        'district': district,
        'ward': ward,
        'variety': variety,
        'latitude': latitude,
        'longitude': longitude,
        'planting_date': plantingDate,
        'fertilizer_kg_per_ha': fertilizerKgPerHa,
        'soil_moisture': soilMoisture,
        'ph_level': phLevel,
        'notes': notes,
        'created_at': createdAt,
        'is_synced': isSynced ? 1 : 0,
      };

  // Build from SQLite row
  factory FieldRecord.fromMap(Map<String, dynamic> map) => FieldRecord(
        id: map['id'],
        officerName: map['officer_name'],
        district: map['district'],
        ward: map['ward'],
        variety: map['variety'],
        latitude: map['latitude'],
        longitude: map['longitude'],
        plantingDate: map['planting_date'],
        fertilizerKgPerHa: map['fertilizer_kg_per_ha'],
        soilMoisture: map['soil_moisture'],
        phLevel: map['ph_level'],
        notes: map['notes'],
        createdAt: map['created_at'],
        isSynced: map['is_synced'] == 1,
      );

  FieldRecord copyWith({bool? isSynced}) => FieldRecord(
        id: id,
        officerName: officerName,
        district: district,
        ward: ward,
        variety: variety,
        latitude: latitude,
        longitude: longitude,
        plantingDate: plantingDate,
        fertilizerKgPerHa: fertilizerKgPerHa,
        soilMoisture: soilMoisture,
        phLevel: phLevel,
        notes: notes,
        createdAt: createdAt,
        isSynced: isSynced ?? this.isSynced,
      );
}

// ── Database helper ──────────────────────────────────────────────────────────
class FieldDatabase {
  static final FieldDatabase instance = FieldDatabase._internal();
  static Database? _db;

  FieldDatabase._internal();

  Future<Database> get database async {
    if (_db != null) return _db!;
    _db = await _initDatabase();
    return _db!;
  }

  Future<Database> _initDatabase() async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, 'agritex_field_logs.db');

    return openDatabase(
      path,
      version: 1,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE field_records (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            officer_name     TEXT    NOT NULL,
            district         TEXT    NOT NULL,
            ward             TEXT    NOT NULL,
            variety          TEXT    NOT NULL,
            latitude         REAL    NOT NULL,
            longitude        REAL    NOT NULL,
            planting_date    TEXT    NOT NULL,
            fertilizer_kg_per_ha REAL NOT NULL,
            soil_moisture    REAL    NOT NULL,
            ph_level         REAL    NOT NULL,
            notes            TEXT    DEFAULT '',
            created_at       TEXT    NOT NULL,
            is_synced        INTEGER DEFAULT 0
          )
        ''');
      },
    );
  }

  // ── INSERT ──
  Future<int> insertRecord(FieldRecord record) async {
    final db = await database;
    return db.insert('field_records', record.toMap());
  }

  // ── READ ALL ──
  Future<List<FieldRecord>> getAllRecords() async {
    final db = await database;
    final rows = await db.query(
      'field_records',
      orderBy: 'created_at DESC',
    );
    return rows.map(FieldRecord.fromMap).toList();
  }

  // ── READ UNSYNCED ONLY (for background sync) ──
  Future<List<FieldRecord>> getUnsyncedRecords() async {
    final db = await database;
    final rows = await db.query(
      'field_records',
      where: 'is_synced = ?',
      whereArgs: [0],
      orderBy: 'created_at ASC',
    );
    return rows.map(FieldRecord.fromMap).toList();
  }

  // ── MARK AS SYNCED ──
  Future<void> markAsSynced(int id) async {
    final db = await database;
    await db.update(
      'field_records',
      {'is_synced': 1},
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  // ── DELETE ──
  Future<void> deleteRecord(int id) async {
    final db = await database;
    await db.delete('field_records', where: 'id = ?', whereArgs: [id]);
  }

  // ── COUNT UNSYNCED ──
  Future<int> countUnsynced() async {
    final db = await database;
    final result = await db.rawQuery(
      'SELECT COUNT(*) as count FROM field_records WHERE is_synced = 0',
    );
    return Sqflite.firstIntValue(result) ?? 0;
  }
}