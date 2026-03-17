import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart'; // kIsWeb
import 'package:google_fonts/google_fonts.dart';
import 'package:geolocator/geolocator.dart';
import 'package:intl/intl.dart';
import '../database/field_database.dart';

class DataEntryScreen extends StatefulWidget {
  const DataEntryScreen({super.key});

  @override
  State<DataEntryScreen> createState() => _DataEntryScreenState();
}

class _DataEntryScreenState extends State<DataEntryScreen> {
  final _formKey = GlobalKey<FormState>();
  bool _isLocating = false;
  bool _isSaving   = false;

  final _farmerCtrl    = TextEditingController();
  final _wardCtrl       = TextEditingController();
  final _moistureCtrl   = TextEditingController();
  final _phCtrl         = TextEditingController();
  final _fertilizerCtrl = TextEditingController();
  final _notesCtrl      = TextEditingController();

  double? _lat;
  double? _lon;

  String _selectedVariety  = 'SC 301';
  String _selectedDistrict = 'Umzingwane';
  DateTime _plantingDate   = DateTime.now();

  final List<String> _varieties = ['SC 301', 'SC 529', 'Pioneer Hybrid'];
  final List<String> _districts = ['Umzingwane', 'Mazabuka', 'Chirundu', 'Guruve'];

  @override
  void dispose() {
    _farmerCtrl.dispose();
    _wardCtrl.dispose();
    _moistureCtrl.dispose();
    _phCtrl.dispose();
    _fertilizerCtrl.dispose();
    _notesCtrl.dispose();
    super.dispose();
  }

  // ── GPS — mobile only ──────────────────────────────────────────────────────
  Future<void> _getLocation() async {
    if (kIsWeb) {
      // On web, use browser geolocation via a simple prompt
      _showSnack('GPS capture is best on mobile. Enter coordinates manually if needed.');
      return;
    }

    setState(() => _isLocating = true);
    try {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        _showSnack('Enable GPS in device settings.');
        setState(() => _isLocating = false);
        return;
      }

      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
      }
      if (permission == LocationPermission.denied ||
          permission == LocationPermission.deniedForever) {
        _showSnack('Location permission denied.');
        setState(() => _isLocating = false);
        return;
      }

      final position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
      );
      setState(() {
        _lat = position.latitude;
        _lon = position.longitude;
        _isLocating = false;
      });
      _showSnack('📍 GPS: ${_lat!.toStringAsFixed(5)}, ${_lon!.toStringAsFixed(5)}');
    } catch (e) {
      setState(() => _isLocating = false);
      _showSnack('Location error: $e');
    }
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _plantingDate,
      firstDate: DateTime(2024),
      lastDate: DateTime.now().add(const Duration(days: 365)),
      builder: (context, child) => Theme(
        data: Theme.of(context).copyWith(
          colorScheme: const ColorScheme.light(primary: Color(0xFF2E7D32)),
        ),
        child: child!,
      ),
    );
    if (picked != null) setState(() => _plantingDate = picked);
  }

  // ── Save — SQLite on mobile, show message on web ───────────────────────────
  Future<void> _saveRecord() async {
    if (!_formKey.currentState!.validate()) return;

    if (kIsWeb) {
      _showSnack('Record saving works on mobile. Install on Android/iOS to save offline.');
      return;
    }

    if (_lat == null || _lon == null) {
      _showSnack('Please capture GPS coordinates first.');
      return;
    }

    setState(() => _isSaving = true);

    final record = FieldRecord(
      farmerName: _farmerCtrl.text.trim(),
      district: _selectedDistrict,
      ward: _wardCtrl.text.trim(),
      variety: _selectedVariety,
      latitude: _lat!,
      longitude: _lon!,
      plantingDate: DateFormat('yyyy-MM-dd').format(_plantingDate),
      fertilizerKgPerHa: double.parse(_fertilizerCtrl.text),
      soilMoisture: double.parse(_moistureCtrl.text),
      phLevel: double.parse(_phCtrl.text),
      notes: _notesCtrl.text.trim(),
      createdAt: DateTime.now().toIso8601String(),
      isSynced: false,
    );

    await FieldDatabase.instance.insertRecord(record);
    setState(() => _isSaving = false);
    _resetForm();

    if (mounted) {
      showDialog(
        context: context,
        builder: (_) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          title: const Text('✅ Record Saved'),
          content: const Text(
            'Field data saved locally.\n\n'
            'It will automatically sync when you are back online.',
          ),
          actions: [
            ElevatedButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('OK'),
            ),
          ],
        ),
      );
    }
  }

  void _resetForm() {
    _formKey.currentState?.reset();
    for (final c in [_farmerCtrl, _wardCtrl, _moistureCtrl,
                     _phCtrl, _fertilizerCtrl, _notesCtrl]) {
      c.clear();
    }
    setState(() {
      _lat = null; _lon = null;
      _plantingDate = DateTime.now();
      _selectedVariety = 'SC 301';
      _selectedDistrict = 'Umzingwane';
    });
  }

  void _showSnack(String msg) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: Text(msg),
      backgroundColor: const Color(0xFF2E7D32),
      behavior: SnackBarBehavior.floating,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
    ));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F0E8),
      appBar: AppBar(title: const Text('📋 New Field Entry')),
      body: Form(
        key: _formKey,
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [

              // Web notice
              if (kIsWeb) ...[
                Container(
                  padding: const EdgeInsets.all(14),
                  margin: const EdgeInsets.only(bottom: 16),
                  decoration: BoxDecoration(
                    color: const Color(0xFFE3F2FD),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: const Color(0xFF90CAF9)),
                  ),
                  child: const Row(
                    children: [
                      Icon(Icons.smartphone, color: Color(0xFF1565C0), size: 18),
                      SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          'GPS capture and offline saving require the mobile app. '
                          'You can preview the form here.',
                          style: TextStyle(fontSize: 12, color: Color(0xFF1565C0)),
                        ),
                      ),
                    ],
                  ),
                ),
              ],

              _SectionHeader('👤 Farmer Details'),
              _buildTextField(_farmerCtrl, 'Farmer Name', Icons.person_outline),
              const SizedBox(height: 12),

              _SectionHeader('📍 Location'),
              DropdownButtonFormField<String>(
                value: _selectedDistrict,
                decoration: _dropDeco('District', Icons.map_outlined),
                items: _districts
                    .map((d) => DropdownMenuItem(value: d, child: Text(d)))
                    .toList(),
                onChanged: (v) => setState(() => _selectedDistrict = v!),
              ),
              const SizedBox(height: 12),
              _buildTextField(_wardCtrl, 'Ward (e.g. Ward 5)', Icons.location_city_outlined),
              const SizedBox(height: 12),

              // GPS row
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: _lat != null
                        ? const Color(0xFF4CAF50)
                        : const Color(0xFFA5D6A7),
                  ),
                ),
                child: Row(
                  children: [
                    Icon(
                      _lat != null ? Icons.gps_fixed : Icons.gps_not_fixed,
                      color: _lat != null
                          ? const Color(0xFF2E7D32)
                          : const Color(0xFF888888),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        _lat != null
                            ? '${_lat!.toStringAsFixed(5)}, ${_lon!.toStringAsFixed(5)}'
                            : kIsWeb
                                ? 'GPS available on mobile only'
                                : 'Tap Capture to get GPS',
                        style: TextStyle(
                          fontSize: 13,
                          color: _lat != null
                              ? const Color(0xFF1B5E20)
                              : const Color(0xFF888888),
                        ),
                      ),
                    ),
                    if (!kIsWeb)
                      TextButton(
                        onPressed: _isLocating ? null : _getLocation,
                        child: _isLocating
                            ? const SizedBox(
                                width: 16, height: 16,
                                child: CircularProgressIndicator(strokeWidth: 2))
                            : const Text('Capture',
                                style: TextStyle(
                                    color: Color(0xFF2E7D32),
                                    fontWeight: FontWeight.w700)),
                      ),
                  ],
                ),
              ),

              const SizedBox(height: 20),
              _SectionHeader('🌱 Crop Details'),
              DropdownButtonFormField<String>(
                value: _selectedVariety,
                decoration: _dropDeco('Maize Variety', Icons.grass_outlined),
                items: _varieties
                    .map((v) => DropdownMenuItem(value: v, child: Text(v)))
                    .toList(),
                onChanged: (v) => setState(() => _selectedVariety = v!),
              ),
              const SizedBox(height: 12),
              InkWell(
                onTap: _pickDate,
                borderRadius: BorderRadius.circular(12),
                child: InputDecorator(
                  decoration: _dropDeco('Planting Date', Icons.calendar_today_outlined),
                  child: Text(DateFormat('dd MMM yyyy').format(_plantingDate),
                      style: const TextStyle(fontSize: 15)),
                ),
              ),
              const SizedBox(height: 12),
              _buildNumberField(_fertilizerCtrl,
                  'Fertilizer Applied (kg/ha)', Icons.science_outlined),

              const SizedBox(height: 20),
              _SectionHeader('🧪 Soil Readings'),
              _buildNumberField(_moistureCtrl,
                  'Soil Moisture (%)', Icons.water_drop_outlined),
              const SizedBox(height: 12),
              _buildNumberField(_phCtrl, 'Soil pH Level',
                  Icons.thermostat_outlined, hint: 'e.g. 6.5'),

              const SizedBox(height: 20),
              _SectionHeader('📝 Notes (Optional)'),
              TextFormField(
                controller: _notesCtrl,
                maxLines: 3,
                decoration: InputDecoration(
                  hintText: 'Any additional observations...',
                  border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12)),
                  filled: true,
                  fillColor: Colors.white,
                ),
              ),

              const SizedBox(height: 28),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: _isSaving ? null : _saveRecord,
                  icon: _isSaving
                      ? const SizedBox(width: 18, height: 18,
                          child: CircularProgressIndicator(
                              strokeWidth: 2, color: Colors.white))
                      : const Icon(Icons.save_outlined),
                  label: Text(_isSaving ? 'Saving...' : 'Save Field Record'),
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    textStyle: const TextStyle(
                        fontSize: 16, fontWeight: FontWeight.w700),
                  ),
                ),
              ),
              const SizedBox(height: 12),
              Center(
                child: Text(
                  kIsWeb
                      ? 'Install on mobile to save records offline'
                      : 'Saved offline · auto-syncs when online',
                  style: TextStyle(fontSize: 12, color: Colors.grey[500]),
                ),
              ),
              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTextField(TextEditingController c, String label, IconData icon) =>
      TextFormField(
        controller: c,
        decoration: InputDecoration(
          labelText: label,
          prefixIcon: Icon(icon, color: const Color(0xFF2E7D32)),
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
          filled: true, fillColor: Colors.white,
        ),
        validator: (v) => (v == null || v.isEmpty) ? 'Required' : null,
      );

  Widget _buildNumberField(TextEditingController c, String label, IconData icon,
      {String? hint}) =>
      TextFormField(
        controller: c,
        keyboardType: const TextInputType.numberWithOptions(decimal: true),
        decoration: InputDecoration(
          labelText: label, hintText: hint,
          prefixIcon: Icon(icon, color: const Color(0xFF2E7D32)),
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
          filled: true, fillColor: Colors.white,
        ),
        validator: (v) {
          if (v == null || v.isEmpty) return 'Required';
          if (double.tryParse(v) == null) return 'Enter a valid number';
          return null;
        },
      );

  InputDecoration _dropDeco(String label, IconData icon) => InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon, color: const Color(0xFF2E7D32)),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
        filled: true, fillColor: Colors.white,
      );
}

class _SectionHeader extends StatelessWidget {
  final String text;
  const _SectionHeader(this.text);

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 10),
        child: Text(text,
            style: GoogleFonts.playfairDisplay(
                fontSize: 15, fontWeight: FontWeight.w700,
                color: const Color(0xFF0D2B0F))),
      );
}