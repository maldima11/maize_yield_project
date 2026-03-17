import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';

class DBHelper {
  static Database? _db;

  Future<Database> get db async {
    if (_db != null) return _db!;
    _db = await initDb();
    return _db!;
  }

  initDb() async {
    String path = join(await getDatabasesPath(), "agritex.db");
    return await openDatabase(path, version: 1, onCreate: (db, version) {
      return db.execute(
        "CREATE TABLE logs(id INTEGER PRIMARY KEY, district TEXT, ward TEXT, variety TEXT, lat REAL, lon REAL, synced INTEGER DEFAULT 0)"
      );
    });
  }

  Future<void> insertLog(Map<String, dynamic> data) async {
    final dbClient = await db;
    await dbClient.insert('logs', data);
  }

  Future<List<Map<String, dynamic>>> getUnsyncedLogs() async {
    final dbClient = await db;
    return await dbClient.query('logs', where: "synced = 0");
  }

  Future<void> markAsSynced(int id) async {
    final dbClient = await db;
    await dbClient.update('logs', {'synced': 1}, where: "id = ?", whereArgs: [id]);
  }
}