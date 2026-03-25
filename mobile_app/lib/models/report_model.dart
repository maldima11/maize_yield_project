class ReportModel {
  final int? id;
  final String district;
  final String ward;
  final String variety;
  final double lat;
  final double lon;
  final int synced; // 0 for false, 1 for true (SQLite doesn't have Boolean)

  ReportModel({
    this.id,
    required this.district,
    required this.ward,
    required this.variety,
    required this.lat,
    required this.lon,
    this.synced = 0,
  });

  // Convert a Report object into a Map to store in SQLite or send to Flask
  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'district': district,
      'ward': ward,
      'variety': variety,
      'lat': lat,
      'lon': lon,
      'synced': synced,
    };
  }

  // Extract a Report object from a Map (Database row)
  factory ReportModel.fromMap(Map<String, dynamic> map) {
    return ReportModel(
      id: map['id'],
      district: map['district'],
      ward: map['ward'],
      variety: map['variety'],
      lat: map['lat'],
      lon: map['lon'],
      synced: map['synced'] ?? 0,
    );
  }

  // Helper for your Flask API JSON format
  Map<String, dynamic> toJson() {
    return {
      "district": district,
      "ward": ward,
      "variety": variety,
      "gps": {"lat": lat, "lon": lon},
      "timestamp": DateTime.now().toIso8601String(),
    };
  }
}