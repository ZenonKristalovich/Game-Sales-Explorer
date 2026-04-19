import sys

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QVBoxLayout, QFrame,
    QLabel, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QLineEdit,
    QSizePolicy, QFileDialog, QFormLayout, QSplitter
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIntValidator, QIcon
from sqlGames import get_genres, get_publishers, get_platforms, run_query
import csv

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class App(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Game Sales Explorer")
        self.setGeometry(100, 100, 1200, 700)

        # Main container
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)

        # ======================
        # SIDEBAR
        # ======================
        sidebar = QFrame()
        sidebar.setFixedWidth(300)
        sidebar_layout = QVBoxLayout()
        sidebar.setLayout(sidebar_layout)
        sidebar_layout.setSpacing(15)

        title = QLabel("Filter Options")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        sidebar_layout.addWidget(title)


        #Run Query Button to Search
        run_btn = QPushButton("Run Query")
        run_btn.clicked.connect(self.run_query)


        # Form layout for filters
        filter_form = QFormLayout()
        filter_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        filter_form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        filter_form.setHorizontalSpacing(10)
        filter_form.setVerticalSpacing(12)

        #Make Limit Input
        self.limit_input = QLineEdit()
        self.limit_input.setValidator(QIntValidator(1, 1000))
        self.limit_input.setText("100")
        self.limit_input.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        # Title input
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter game title...")
        self.title_input.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        # Genre input
        self.genre_input = QComboBox()
        self.genre_input.setEditable(True)
        self.genre_input.addItems(get_genres())
        self.genre_input.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        # Publisher input
        self.publisher_input = QComboBox()
        self.publisher_input.setEditable(True)
        self.publisher_input.addItems(get_publishers())
        self.publisher_input.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        # Platform input
        self.platform_input = QComboBox()
        self.platform_input.setEditable(True)
        self.platform_input.addItems(get_platforms())
        self.platform_input.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        # Add rows
        filter_form.addRow("Result Limit", self.limit_input)
        filter_form.addRow("Title", self.title_input)
        filter_form.addRow("Genre", self.genre_input)
        filter_form.addRow("Publisher", self.publisher_input)
        filter_form.addRow("Platform", self.platform_input)


        #Reset Button
        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self.reset_filters)

        #Create CSV Export Button
        csv_export_btn = QPushButton("Export to CSV")
        csv_export_btn.clicked.connect(self.export_to_csv)

        #Adding Widgets to Sidebar

        sidebar_layout.addLayout(filter_form)

        sidebar_layout.addStretch()  # pushes everything up

        sidebar_layout.addWidget(run_btn)
        sidebar_layout.addWidget(reset_btn)
        sidebar_layout.addWidget(csv_export_btn)
        

        # ======================
        # MAIN CONTENT
        # ======================
        content = QFrame()
        content_layout = QVBoxLayout()
        content.setLayout(content_layout)

        header = QLabel("Dashboard")
        header.setStyleSheet("font-size: 20px; font-weight: bold;")
        
        
        info = QLabel("Sales in Millions of Copies Sold")
        info.setStyleSheet("font-size: 16px; font-weight: bold;")

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "Rank", "Name", "Platform", "Year", "Publisher", "Genre", "NA Sales", "EU Sales", "JP Sales", "Other Sales", "Global Sales"
        ])

        self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(28)
        self.table.verticalHeader().setVisible(False)


        #Graph

        self.figure = Figure(figsize=(5, 3))
        self.figure.patch.set_facecolor("#1e2d44")
        self.canvas = FigureCanvas(self.figure)

        graph_frame = QFrame()
        graph_frame.setStyleSheet("""
        QFrame {
            background-color: #1e2d44;
            border-radius: 20px;
            padding: 10px;
        }
        """)

        graph_layout = QVBoxLayout()
        graph_layout.addWidget(self.canvas)
        graph_frame.setLayout(graph_layout)


        #Add Graph to Content Layout
        content_layout.addWidget(header)
        content_layout.addWidget(info)

        #Create Splitter
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.table)
        splitter.addWidget(graph_frame)

        splitter.setSizes([700, 500])  # starting heights
        content_layout.addWidget(splitter)

        # ======================
        # ADD TO MAIN LAYOUT
        # ======================
        main_layout.addWidget(sidebar)
        main_layout.addWidget(content)

        # Apply dark theme
        self.setStyleSheet(self.get_styles())

        # Load data
        


    # ======================
    # RUN QUERY
    # ======================
    def run_query(self):
        limit = self.limit_input.text()
        title = self.title_input.text()
        genre = self.genre_input.currentText()
        publisher = self.publisher_input.currentText()
        platform = self.platform_input.currentText()
        data = run_query(limit, title, genre, publisher, platform)

        self.update_chart(data)
        
        self.table.setRowCount(len(data))  # number of rows

        self.populate_table(data)
        self.table.resizeColumnToContents(1)

    def update_chart(self, results):
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        if not results:
            ax.set_title("No data to display")
            self.canvas.draw()
            return

        publisher_totals = {}

        for row in results:
            publisher = row[4]      # publisher
            global_sales = row[10]  # global_sales

            if publisher not in publisher_totals:
                publisher_totals[publisher] = 0

            publisher_totals[publisher] += global_sales if global_sales else 0

        sorted_data = sorted(
            publisher_totals.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        publishers = [item[0] for item in sorted_data]
        sales = [item[1] for item in sorted_data]

        publishers.reverse()
        sales.reverse()

        ax.barh(publishers, sales)
        ax.set_title("Top Publishers by Global Sales")
        ax.set_xlabel("Millions Sold")

        self.figure.subplots_adjust(left=0.25, right=0.95, top=0.88, bottom=0.12)
        self.figure.patch.set_facecolor("#ffffff")
        self.canvas.draw()

    # ======================
    # RESET FILTERS
    # ======================
    def reset_filters(self):
        self.limit_input.setText("100")
        self.title_input.setText("")
        self.genre_input.setCurrentText("--None--")
        self.publisher_input.setCurrentText("--None--")
        self.platform_input.setCurrentText("--None--")

        #Reset Graph
        self.figure.clear()
        self.figure.patch.set_facecolor("#1e2d44")
        self.canvas.draw()

    # ======================
    # EXPORT TO CSV
    # ======================
    def export_to_csv(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save CSV File",
            "",
            "CSV Files (*.csv)"
        )

        if file_path:
            with open(file_path, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)

                # Write column headers
                headers = []
                for col in range(self.table.columnCount()):
                    headers.append(self.table.horizontalHeaderItem(col).text())

                writer.writerow(headers)

                # Write table data
                for row in range(self.table.rowCount()):
                    row_data = []

                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)

                        if item:
                            row_data.append(item.text())
                        else:
                            row_data.append("")

                    writer.writerow(row_data)

    # ======================
    # TABLE POPULATION
    # ======================

    def populate_table(self, data):
        self.table.setSortingEnabled(False)

        self.table.setRowCount(len(data))

        if not data:
            return

        # -1 because we skip the id column
        self.table.setColumnCount(len(data[0]) - 1)

        headers = [
            "Rank", "Name", "Platform", "Year", "Publisher", "Genre",
            "NA Sales", "EU Sales", "JP Sales", "Other Sales", "Global Sales"
        ]
        self.table.setHorizontalHeaderLabels(headers)

        # FIXED column indexes (after removing id)
        numeric_int_cols = {0, 3}       # Rank, Year
        numeric_float_cols = {6, 7, 8, 9, 10}

        for i, row in enumerate(data):
            for j, value in enumerate(row):  # 👈 skip ID
                item = QTableWidgetItem()

                if value is None:
                    item.setText("")
                
                elif j in numeric_int_cols:
                    item.setData(Qt.ItemDataRole.DisplayRole, int(value))
                
                elif j in numeric_float_cols:
                    item.setData(Qt.ItemDataRole.DisplayRole, float(value))
                
                else:
                    item.setText(str(value))

                if j in numeric_int_cols or j in numeric_float_cols:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                
                if j in {0, 3}:  # Rank, Year
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                self.table.setItem(i, j, item)

        self.table.setSortingEnabled(True)
    # ======================
    # STYLING
    # ======================
    def get_styles(self):
        return """
        QMainWindow {
            background-color: #0f172a;
        }

        QFrame {
            background-color: #1e293b;
            border-radius: 10px;
        }

        QLabel {
            color: white;
        }

        QPushButton {
            background-color: #3b82f6;
            color: white;
            padding: 8px;
            border-radius: 6px;
        }

        QPushButton:hover {
            background-color: #2563eb;
        }

        QComboBox, QSpinBox {
            background-color: #334155;
            color: white;
            padding: 5px;
            border-radius: 5px;
        }

        QTableWidget {
            background-color: #0f172a;
            color: white;
            gridline-color: #334155;
        }
        """


# ======================
# RUN APP
# ======================
app = QApplication(sys.argv)
app.setWindowIcon(QIcon("Icon.png"))

window = App()
window.show()
app.exec()