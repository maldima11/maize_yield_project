import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import '../models/report_model.dart';

class DBHelper {
  static Database? _db;

  Future<Database> get db async {
    if (_db != null) return _db!;
    _db = await initDb();
    return _db!;
  }

  initDb() async {
    String path = join(await getDatabasesPath(), "agritex_v1.db");
    return await openDatabase(path, version: 1, onCreate: (db, version) {
      return db.execute(
        "CREATE TABLE reports(id INTEGER PRIMARY KEY AUTOINCREMENT, district TEXT, ward TEXT, variety TEXT, lat REAL, lon REAL, synced INTEGER DEFAULT 0)"
      );
    });
  }

  Future<int> insertReport(ReportModel report) async {
    final dbClient = await db;
    return await dbClient.insert('reports', report.toMap());
  }

  Future<List<ReportModel>> getUnsyncedReports() async {
    final dbClient = await db;
    final List<Map<String, dynamic>> maps = await dbClient.query('reports', where: "synced = 0");
    return List.generate(maps.length, (i) => ReportModel.fromMap(maps[i]));
  }

  Future<void> markAsSynced(int id) async {
    final dbClient = await db;
    await dbClient.update('reports', {'synced': 1}, where: "id = ?", whereArgs: [id]);
  }
}