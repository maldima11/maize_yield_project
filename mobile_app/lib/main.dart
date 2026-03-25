import 'package:flutter/material.dart';
import 'package:workmanager/workmanager.dart';
import 'screens/input_form.dart';
import 'data/sync_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize Background Sync
  Workmanager().initialize(callbackDispatcher, isInDebugMode: true);
  
  // Register a periodic task (runs every 15 mins)
  Workmanager().registerPeriodicTask(
    "agritex-sync-task",
    "simplePeriodicTask",
    frequency: Duration(minutes: 15),
    constraints: Constraints(networkType: NetworkType.connected),
  );

  runApp(AgritexApp());
}

class AgritexApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Agritex Mobile',
      theme: ThemeData(primarySwatch: Colors.green),
      home: InputForm(),
    );
  }
}