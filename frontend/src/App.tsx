import { useState } from "react";
import { AppShell } from "./components/AppShell";
import { analyzeFoodImage, getMockAnalysis, getMockPrediction, predictGlucose } from "./lib/api";
import { AnalysisPage } from "./pages/AnalysisPage";
import { HistoryPage } from "./pages/HistoryPage";
import { HomePage } from "./pages/HomePage";
import { PredictionPage } from "./pages/PredictionPage";
import { SettingsPage } from "./pages/SettingsPage";
import {
  AnalysisResult,
  GlucosePredictionResult,
  PageKey,
  makeSampleCgmPayload,
} from "./data/mockData";

export default function App() {
  const [page, setPage] = useState<PageKey>("home");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string>();
  const [analysis, setAnalysis] = useState<AnalysisResult>(getMockAnalysis());
  const [prediction, setPrediction] = useState<GlucosePredictionResult>(getMockPrediction());
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [predictionLoading, setPredictionLoading] = useState(false);

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return;
    setAnalysisLoading(true);
    const [result] = await Promise.all([
      analyzeFoodImage(selectedFile),
      new Promise((resolve) => setTimeout(resolve, 800)),
    ]);
    setAnalysis(result);
    setAnalysisLoading(false);
    setPage("analysis");
  };

  const handlePrediction = async () => {
    setPredictionLoading(true);
    const result = await predictGlucose(makeSampleCgmPayload());
    setPrediction(result);
    setPredictionLoading(false);
    setPage("prediction");
  };

  const renderPage = () => {
    if (page === "analysis") {
      return <AnalysisPage analysis={analysis} onPrediction={handlePrediction} />;
    }
    if (page === "prediction") {
      return <PredictionPage prediction={prediction} onRefresh={handlePrediction} isLoading={predictionLoading} />;
    }
    if (page === "history") {
      return <HistoryPage />;
    }
    if (page === "settings") {
      return <SettingsPage />;
    }
    return (
      <HomePage
        previewUrl={previewUrl}
        isLoading={analysisLoading}
        onFileSelect={handleFileSelect}
        onAnalyze={handleAnalyze}
      />
    );
  };

  return (
    <AppShell currentPage={page} onNavigate={setPage}>
      {renderPage()}
    </AppShell>
  );
}
