import axios from "axios";
import { BridgeInput, AnalysisResult } from "../types/bridge";

const API_BASE = "http://127.0.0.1:8000";

export async function analyzeBridge(
  data: BridgeInput
): Promise<AnalysisResult> {

  const response = await axios.post(
    `${API_BASE}/bridge/analyze`,
    data
  );

  return response.data;
}