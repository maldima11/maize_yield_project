import 'package:workmanager/workmanager.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'db_helper.dart';
import '../core/constants.dart';

@pragma('vm:entry-point')
void callbackDispatcher() {
  Workmanager().executeTask((task, inputData) async {
    final db = DBHelper();
    final unsynced = await db.getUnsyncedReports();

    for (var report in unsynced) {
      try {
        final response = await http.post(
          Uri.parse("${AppConstants.baseUrl}/predict_yield"),
          headers: {"Content-Type": "application/json"},
          body: jsonEncode(report.toJson()),
        );

        if (response.statusCode == 200) {
          await db.markAsSynced(report.id!);
          print("Synced Report ID: ${report.id}");
        }
      } catch (e) {
        print("Sync Error: $e");
      }
    }
    return Future.value(true);
  });
}