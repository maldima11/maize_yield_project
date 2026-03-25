import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import '../data/db_helper.dart';
import '../models/report_model.dart';

class InputForm extends StatefulWidget {
  @override
  _InputFormState createState() => _InputFormState();
}

class _InputFormState extends State<InputForm> {
  final _db = DBHelper();
  final _districtController = TextEditingController();
  final _wardController = TextEditingController();
  String _selectedVariety = "SC 301";

  Future<void> _saveData() async {
    // 1. Get GPS
    LocationPermission permission = await Geolocator.requestPermission();
    Position pos = await Geolocator.getCurrentPosition();

    // 2. Create Model
    ReportModel report = ReportModel(
      district: _districtController.text,
      ward: _wardController.text,
      variety: _selectedVariety,
      lat: pos.latitude,
      lon: pos.longitude,
    );

    // 3. Save to SQLite
    await _db.insertReport(report);
    
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text("Saved Offline. Will sync when online.")),
    );
    
    _districtController.clear();
    _wardController.clear();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("New Extension Log")),
      body: Padding(
        padding: EdgeInsets.all(16.0),
        child: Column(
          children: [
            TextField(controller: _districtController, decoration: InputDecoration(labelText: "District")),
            TextField(controller: _wardController, decoration: InputDecoration(labelText: "Ward")),
            DropdownButton<String>(
              value: _selectedVariety,
              items: ["SC 301", "SC 719", "SC 513"].map((v) => DropdownMenuItem(value: v, child: Text(v))).toList(),
              onChanged: (val) => setState(() => _selectedVariety = val!),
            ),
            SizedBox(height: 30),
            ElevatedButton(onPressed: _saveData, child: Text("Capture GPS & Save Offline")),
          ],
        ),
      ),
    );
  }
}