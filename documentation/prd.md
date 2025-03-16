### **Product Requirements Document (PRD)**  
## **1. Produktübersicht**
### **1.1 Ziel des Systems**
Das Dokumenten-Informationssystem automatisiert die Verarbeitung von Rechnungen mithilfe eines **hierarchischen Multi-Agenten-Systems** basierend auf **Smolagents**. Das System extrahiert Texte aus Rechnungen, konvertiert sie in ein strukturiertes Markdown-Format und verarbeitet die Daten für die weitere Nutzung.

### **1.2 Anwendungsfälle**
Das System wird für Unternehmen und Buchhaltungssoftware-Anbieter entwickelt, um Rechnungsdokumente effizient zu verarbeiten.  
Hauptanwendungsfälle:  
- **Automatische Texterkennung und Konvertierung in Markdown**  
- **Strukturierte Darstellung von Rechnungsinhalten**  
- **Extraktion von Rechnungsnummern, Datum, Beträgen und LineItems**  
- **Validierung und Datenabgleich mit bestehenden Buchhaltungsinformationen**  
- **Integration in bestehende ERP- und Buchhaltungssysteme**  

### **1.3 Vorteile des Systems**
✅ **Automatisierte Dokumentenverarbeitung** → Reduziert manuellen Aufwand  
✅ **Standardisiertes Markdown-Format** → Vereinfacht die Weiterverarbeitung  
✅ **Strukturierte Datenextraktion** → Bereit für die Buchhaltung  
✅ **Skalierbare Architektur** → Verarbeitet große Mengen an Dokumenten parallel  
✅ **Erweiterbarkeit** → Anpassung an verschiedene Dokumenttypen  

---

## **2. Systemanforderungen**
### **2.1 Funktionale Anforderungen**
| **ID**  | **Anforderung** | **Beschreibung** |
|---------|---------------|----------------|
| F-01 | **Markdown-Agent** | Konvertiert Dokumente in strukturiertes Markdown unter Verwendung von Azure OCR und LLM. |
| F-02 | **Extraktions-Agent** | Verarbeitet Markdown-Text und extrahiert relevante Daten. |
| F-03 | **Manager-Agent** | Orchestriert die Dokumentenverarbeitung und aggregiert die Ergebnisse. |
| F-04 | **Mehrformat-Unterstützung** | PDFs, Scans und Bilddateien müssen verarbeitet werden können. |
| F-05 | **Validierung & Abgleich** | Rechnungsdaten sollen mit bestehenden Systemdaten abgeglichen werden können. |
| F-06 | **Anpassbare Markdown-Templates** | Unterstützung für verschiedene Dokumentformate und -layouts. |

### **2.2 Nicht-funktionale Anforderungen**
| **ID**  | **Anforderung** | **Beschreibung** |
|---------|---------------|----------------|
| NF-01 | **Skalierbarkeit** | System muss parallel mehrere Dokumente verarbeiten können. |
| NF-02 | **Performance** | Ein Dokument sollte in unter **5 Sekunden** verarbeitet werden. |
| NF-03 | **Sicherheit** | Alle verarbeiteten Daten müssen isoliert und geschützt sein. |
| NF-04 | **Monitoring & Logging** | OpenTelemetry zur Überwachung der Agenten. |

---

## **3. Systemarchitektur**
### **3.1 Architekturübersicht**
Das System basiert auf einem **hierarchischen Multi-Agenten-Ansatz** mit **Smolagents**. Die Architektur umfasst folgende Agenten:  

🔹 **Manager-Agent**  
- Steuert die Verarbeitung des Dokuments.  
- Ruft den Markdown-Agenten zur Dokumentenkonvertierung auf.  
- Übergibt das Markdown an den Extraktions-Agenten.  
- Aggregiert die extrahierten Daten und gibt sie zurück.  

🔹 **Markdown-Agent**  
- Nutzt **Azure Read OCR**, um den Text aus dem Dokument zu extrahieren.  
- Verwendet LLM zur Konvertierung des OCR-Texts in strukturiertes Markdown.  
- Implementiert Templates für verschiedene Dokumenttypen.  
- Gibt das formatierte Markdown zurück.  

🔹 **Extraktions-Agent**  
- Analysiert das Markdown und extrahiert strukturierte Daten (z. B. Rechnungsnummer, Betrag, Datum, LineItems).  
- Gibt das Ergebnis als strukturiertes JSON zurück.  

---

## **4. Implementierung**
### **4.1 Markdown-Agent**
Der **Markdown-Agent** kombiniert **Azure Read OCR** und LLM, um Dokumente in strukturiertes Markdown zu konvertieren.  
**Technologien**: Smolagents, Azure OCR API, LLM  

```python
from smolagents import ToolCallingAgent, Tool
from smolagents.models import Model
from src.tools.azure_ocr_tool import AzureOCRTool

class MarkdownAgent(ToolCallingAgent):
    """Agent für die Konvertierung von Dokumenten in strukturiertes Markdown"""
    
    def __init__(
        self,
        model: Model,
        azure_ocr_tool: Optional[AzureOCRTool] = None,
        prompt_templates: Optional[Dict] = None,
        max_steps: int = 5,
        **kwargs
    ):
        # OCR Tool initialisieren
        self.ocr_tool = azure_ocr_tool or AzureOCRTool()
        
        # Tools konfigurieren
        tools = [self.ocr_tool]
        
        # Standardprompts verwenden wenn keine angegeben
        if prompt_templates is None:
            prompt_templates = DEFAULT_MARKDOWN_PROMPT_TEMPLATES
            
        # Elternklasse initialisieren
        super().__init__(
            tools=tools,
            model=model,
            prompt_templates=prompt_templates,
            max_steps=max_steps,
            **kwargs
        )
        
        self.name = "markdown_agent"
        self.description = "Konvertiert Dokumente in strukturiertes Markdown unter Verwendung von OCR und LLM."

    def process_document(
        self, 
        file_path: str,
        template: Optional[str] = None,
        additional_args: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Verarbeitet ein Dokument und konvertiert es in Markdown.
        
        Args:
            file_path: Pfad zum Dokument
            template: Optional, Name des zu verwendenden Templates
            additional_args: Zusätzliche Argumente
            
        Returns:
            str: Formatiertes Markdown
        """
        task = f"""Konvertiere das Dokument in strukturiertes Markdown:
        Pfad: {file_path}
        Template: {template or 'Standard'}
        
        Deine Aufgaben:
        1. Extrahiere den Text mit dem OCR Tool
        2. Strukturiere den Text in sauberes Markdown
        3. Verwende das angegebene Template falls vorhanden
        4. Stelle sicher, dass alle wichtigen Informationen erhalten bleiben
        5. Formatiere Tabellen, Listen und Überschriften korrekt
        
        Bitte verarbeite das Dokument und gib das formatierte Markdown zurück."""

        # Agent ausführen
        result = self.run(
            task=task,
            additional_args={"file_path": file_path, **(additional_args or {})}
        )
        
        return result
```

---

## **5. Beispiel-Durchlauf & Ausgabe**
### **5.1 Eingabe (Rechnung als PDF)**
```plaintext
Rechnung Nr. 12345
Datum: 15. März 2025
Gesamtbetrag: 1.250,00 EUR
```

### **5.2 Markdown-Ausgabe**
```markdown
# Rechnung #12345

**Datum:** 15. März 2025  
**Gesamtbetrag:** 1.250,00 EUR

## Positionen

| Pos | Beschreibung | Menge | Einzelpreis | Gesamt |
|-----|--------------|-------|-------------|--------|
| 1   | Produkt A    | 2     | 500,00 EUR  | 1.000,00 EUR |
| 2   | Service B    | 1     | 250,00 EUR  | 250,00 EUR |

## Zusammenfassung

- Nettobetrag: 1.050,42 EUR
- MwSt (19%): 199,58 EUR
- **Gesamtbetrag: 1.250,00 EUR**
```

### **5.3 Extrahierte JSON-Daten**
```json
{
  "Rechnungsnummer": "12345",
  "Datum": "15.03.2025",
  "Gesamtbetrag": "1250.00 EUR",
  "LineItems": [
    {
      "Position": 1,
      "Beschreibung": "Produkt A",
      "Menge": 2,
      "Einzelpreis": "500.00 EUR",
      "Gesamt": "1000.00 EUR"
    },
    {
      "Position": 2,
      "Beschreibung": "Service B",
      "Menge": 1,
      "Einzelpreis": "250.00 EUR",
      "Gesamt": "250.00 EUR"
    }
  ],
  "MwSt": {
    "Prozent": 19,
    "Betrag": "199.58 EUR"
  },
  "Nettobetrag": "1050.42 EUR"
}
```
