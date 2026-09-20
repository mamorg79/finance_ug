# Finance UG - Benutzerhandbuch

**Einfache Buchhaltung für dein Unternehmen.**

---

## 📌 Schnellstart

### Voraussetzungen
- Python 3.10+
- Django 5.2+
- Datenbank (SQLite, PostgreSQL, MySQL)

### Installation
```bash
# Projekt klonen
git clone https://github.com/mamorg79/finance_ug.git
cd finance_ug

# Virtuelle Umgebung erstellen
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ODER
venv\Scripts\activate  # Windows

# Abhängigkeiten installieren
pip install -r requirements.txt

# Datenbank einrichten
python manage.py migrate

# Admin-Benutzer erstellen
python manage.py createsuperuser

# Server starten
python manage.py runserver
```

**Anwendung öffnen:** [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 🔑 Login

1. **Admin-Zugang:** Nutze den mit `createsuperuser` erstellten Benutzer
2. **Passwort zurücksetzen:** Falls vergessen, nutze `python manage.py changepassword <benutzername>`

---

## 🏠 Dashboard

**Was du siehst:**
- **Aktiva/Passiva/Eigenkapital:** Aktuelle Finanzlage auf einen Blick
- **Kontenstände:** Die 10 wichtigsten Konten mit aktuellem Saldo
- **Letzte Buchungen:** Die neuesten 10 Transaktionen
- **Schnellaktionen:** Direkte Buttons für häufige Aufgaben

**Was du tun kannst:**
- Auf "Alle Konten" klicken → Zur Kontenliste
- Auf "Alle Buchungen" klicken → Zur Buchungsliste
- Schnellaktionen nutzen → Direkte Navigation

---

## 💳 Konten verwalten

### Konten anzeigen
1. **Navigation:** Dashboard → "Alle Konten" ODER Menü → "Buchhaltung" → "Konten"
2. **Liste:** Alle aktiven Konten mit Kontonummer, Name, Typ, Gruppe und Saldo
3. **Suche:** Nutze das Suchfeld für Kontonummer oder Name
4. **Filter:** Wähle Kontenart aus dem Dropdown

### Neues Konto erstellen
1. Klicke auf "Neues Konto" (rechts oben)
2. **Pflichtfelder:**
   - **Kontonummer:** Eindeutige Nummer (z.B. 1000, 2000)
   - **Kontenbezeichnung:** Name des Kontos (z.B. "Bank", "Umsatzsteuer")
   - **Kontenart:** Asset, Passiva, Ertrag, Aufwand
   - **Kontengruppe:** Optional, für bessere Organisation
3. **Speichern:** Klicke auf "Speichern"

### Konto bearbeiten
1. In der Kontenliste: Klicke auf das ⚙️-Symbol (Bearbeiten)
2. Ändere die gewünschten Felder
3. **Speichern:** Klicke auf "Speichern"

### Kontodetails anzeigen
1. Klicke auf die Kontonummer oder das 👁️-Symbol
2. **Was du siehst:**
   - Kontodaten
   - Aktueller Saldo
   - Letzte 20 Buchungen für dieses Konto

---

## 📝 Buchungen erstellen

### Einfache Buchung (1 Soll, 1 Haben)
1. **Navigation:** Dashboard → "Neue Buchung" ODER Menü → "Buchhaltung" → "Buchungen" → "Neue Buchung"
2. **Buchungskopf:**
   - **Datum:** Buchungsdatum (Standard: heute)
   - **Belegnummer:** Eindeutige Nummer (wird automatisch generiert: BKG-000001, BKG-000002, ...)
   - **Belegart:** Wähle aus (Rechnung, Gutschrift, Bank, Kasse, etc.)
   - **Beschreibung:** Kurze Beschreibung (z.B. "Miete Januar")
   - **Referenz:** Optional (z.B. Rechnungsnummer)
3. **Buchungszeile:**
   - **Konto:** Wähle das Konto aus
   - **Seite:** Soll (links) oder Haben (rechts)
   - **Betrag:** Betrag in Euro
   - **Steuersatz:** Optional (19%, 7%, 0%)
   - **Beschreibung:** Optional, spezifisch für diese Zeile
4. **Speichern:** Klicke auf "Speichern"

### Buchung mit mehreren Zeilen
1. Erstelle die Buchung wie oben
2. Nach dem Speichern: Klicke auf "Bearbeiten"
3. Füge weitere Zeilen hinzu (Button "Weitere Zeile hinzufügen" in der Formularansicht)
4. **Wichtig:** Soll = Haben (Buchung muss ausgeglichen sein!)

---

## ✅ Buchungen verwalten

### Buchung anzeigen
1. In der Buchungsliste: Klicke auf die Belegnummer oder das 👁️-Symbol
2. **Was du siehst:**
   - Alle Buchungsdaten
   - Alle Zeilen der Buchung
   - Summen

### Buchung bearbeiten
1. In der Buchungsliste: Klicke auf das ⚙️-Symbol (nur bei ungebuchten Buchungen!)
2. Ändere die gewünschten Felder
3. **Speichern:** Klicke auf "Speichern"

### Buchung löschen
1. In der Buchungsliste: Klicke auf das 🗑️-Symbol (nur bei ungebuchten Buchungen!)
2. **Bestätigen:** Klicke auf "Löschen"

### Buchung buchen (finalisieren)
1. In der Buchungsliste: Klicke auf das ✅-Symbol (nur bei ungebuchten Buchungen!)
2. **Prüfung:** Die Buchung muss ausgeglichen sein (Soll = Haben)
3. **Bestätigen:** Klicke auf "Buchen"
4. **Effekt:**
   - Buchung kann nicht mehr bearbeitet oder gelöscht werden
   - Kontensalden werden aktualisiert

### Buchung stornieren
1. In der Buchungsliste: Klicke auf das 🔄-Symbol (nur bei gebuchten, nicht stornierten Buchungen!)
2. **Bestätigen:** Klicke auf "Stornieren"
3. **Effekt:**
   - Es wird eine Stornobuchung erstellt
   - Originalbuchung wird als storniert markiert
   - Kontensalden werden korrigiert

---

## 📊 Berichte

### Summen- und Saldenliste (Trial Balance)
**Zweck:** Prüfen, ob alle Buchungen ausgeglichen sind

1. **Navigation:** Menü → "Buchhaltung" → "Summen- und Saldenliste"
2. **Was du siehst:**
   - Alle Konten mit Soll- und Habensummen
   - Aktueller Saldo pro Konto
   - **Prüfung:** Soll-Summe = Haben-Summe (muss stimmen!)

### Hauptbuch (General Ledger)
**Zweck:** Chronologische Übersicht aller Buchungen

1. **Navigation:** Menü → "Buchhaltung" → "Hauptbuch"
2. **Was du siehst:** Alle Buchungen in chronologischer Reihenfolge

---

## 📁 Journale

**Zweck:** Buchungen nach Journalen gruppieren (z.B. Bank, Kasse, Rechnungen)

1. **Navigation:** Menü → "Buchhaltung" → "Journale"
2. **Journal anzeigen:** Klicke auf das Journal
3. **Was du siehst:** Alle Einträge in diesem Journal

---

## 🗓️ Buchungsperioden

**Zweck:** Zeiträume für die Buchhaltung definieren (z.B. Geschäftsjahr)

### Periode erstellen
1. **Navigation:** Menü → "Buchhaltung" → "Buchungsperioden" → "Neue Periode"
2. **Felder:**
   - **Name:** z.B. "Geschäftsjahr 2026"
   - **Startdatum:** erster Tag der Periode
   - **Enddatum:** letzter Tag der Periode
3. **Speichern:** Klicke auf "Speichern"

---

## 🔄 Abstimmungen

**Zweck:** Bank- oder Kassenabstimmungen dokumentieren

### Abstimmung erstellen
1. **Navigation:** Menü → "Buchhaltung" → "Abstimmungen" → "Neue Abstimmung"
2. **Felder:**
   - **Konto:** Wähle das abzustimmende Konto
   - **Aussagedatum:** Datum des Kontoauszugs
   - **Anfangsbestand:** Saldo zu Beginn
   - **Endbestand:** Saldo laut Kontoauszug
   - **Buchungssaldo:** Saldo laut Buchhaltung
3. **Speichern:** Klicke auf "Speichern"

---

## 👥 Kontakte verwalten

### Kontakt erstellen
1. **Navigation:** Menü → "Kontakte" → "Neuer Kontakt"
2. **Felder:**
   - **Name:** Firmenname oder Vor-/Nachname
   - **Kontaktart:** Kunde, Lieferant, Sonstiger
   - **Adresse:** Straße, PLZ, Ort
   - **Kontakt:** E-Mail, Telefon
   - **Steuernummer:** Optional
3. **Speichern:** Klicke auf "Speichern"

### Kontakt bearbeiten/löschen
- **Bearbeiten:** ⚙️-Symbol in der Kontaktliste
- **Löschen:** 🗑️-Symbol in der Kontaktliste

---

## 📄 Rechnungen

### Rechnung erstellen
1. **Navigation:** Menü → "Rechnungen" → "Neue Rechnung"
2. **Rechnungskopf:**
   - **Kontakt:** Wähle den Kunden/Lieferanten
   - **Rechnungsnummer:** Eindeutige Nummer
   - **Datum:** Rechnungsdatum
   - **Fälligkeitsdatum:** Zahlungsziel
   - **Rechnungstyp:** Eingangsrechnung (von Lieferanten) oder Ausgangsrechnung (an Kunden)
3. **Rechnungszeilen:**
   - **Beschreibung:** Produkt/Dienstleistung
   - **Menge:** Anzahl
   - **Einzelpreis:** Preis pro Einheit
   - **Steuersatz:** 19%, 7%, 0%
4. **Speichern:** Klicke auf "Speichern"

### Rechnung als gebucht markieren
1. Rechnung öffnen
2. Klicke auf "Als bezahlt markieren"
3. **Effekt:** Rechnung wird als bezahlt markiert

---

## 🎯 Wichtige Regeln

### 1. Doppelte Buchführung
- **Jede Buchung hat mindestens 2 Zeilen:** 1 Soll, 1 Haben
- **Soll = Haben:** Die Summe aller Soll-Beträge muss der Summe aller Haben-Beträge entsprechen

### 2. Kontenplan
- **Aktiva (Vermögen):** Bank, Kasse, Forderungen, Maschinen
- **Passiva (Schulden):** Darlehen, Verbindlichkeiten
- **Erträge (Einnahmen):** Umsatzerlöse, Zinserträge
- **Aufwendungen (Ausgaben):** Miete, Gehälter, Material

### 3. Belegnummern
- Werden automatisch generiert: BKG-000001, BKG-000002, ...
- **Manuell ändern:** Nur wenn nötig (z.B. für externe Belegnummern)

### 4. Gebuchte Buchungen
- **Können nicht bearbeitet oder gelöscht werden**
- **Können nur storniert werden** (erstellt eine Gegenbuchung)

### 5. Stornierte Buchungen
- Werden als storniert markiert
- **Können nicht erneut storniert werden**

---

## ❓ Häufige Probleme & Lösungen

| Problem | Lösung |
|---------|--------|
| **TemplateDoesNotExist** | Template fehlt → Template erstellen oder Installation prüfen |
| **Buchung nicht ausgeglichen** | Soll- und Haben-Beträge prüfen → müssen gleich sein |
| **Konto nicht gefunden** | Konto existiert nicht → Neues Konto erstellen |
| **Keine Berechtigung** | Nicht eingeloggt oder falsche Berechtigungen → Login prüfen |
| **Datenbank-Fehler** | Migrationen fehlen → `python manage.py migrate` ausführen |

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/mamorg79/finance_ug/issues)
- **Dokumentation:** Diese Datei
- **Code:** [GitHub Repository](https://github.com/mamorg79/finance_ug)

---

## 🔒 Sicherheit

- **Backups:** Regelmäßig Datenbank sichern
- **Passwörter:** Sichere Passwörter verwenden
- **Zugang:** Nur autorisierte Personen haben Zugriff

---

**KISS-Prinzip:** Halte es einfach. Diese Dokumentation erklärt nur, was du wirklich brauchst. Kein Ballast, keine Komplexität. Einfach loslegen und buchen!
