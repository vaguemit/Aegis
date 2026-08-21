import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import NetworkGraphView from './components/NetworkGraphView';
import InspectorPanel from './components/InspectorPanel';
import AttackPredictionPanel from './components/AttackPredictionPanel';
import ExplainabilityPanel from './components/ExplainabilityPanel';
import DefenseSimulatorPanel from './components/DefenseSimulatorPanel';
import ScenarioModal from './components/ScenarioModal';
import ExperimentsModal from './components/ExperimentsModal';

export default function App() {
  const [graphs, setGraphs] = useState([]);
  const [selectedGraphId, setSelectedGraphId] = useState('');
  const [graphData, setGraphData] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [selectedModel, setSelectedModel] = useState('gat');

  const [isPredicting, setIsPredicting] = useState(false);
  const [predictionResult, setPredictionResult] = useState(null);
  const [activePathIndex, setActivePathIndex] = useState(0);

  const [explainResult, setExplainResult] = useState(null);
  const [isExplainModalOpen, setIsExplainModalOpen] = useState(false);

  const [defenseResult, setDefenseResult] = useState(null);
  const [recommendations, setRecommendations] = useState([]);

  const [isGenerateModalOpen, setIsGenerateModalOpen] = useState(false);
  const [isExperimentsModalOpen, setIsExperimentsModalOpen] = useState(false);
  const [backendOnline, setBackendOnline] = useState(false);

  // 1. Initial Load: Fetch Graphs and Check Health
  useEffect(() => {
    fetch('/health')
      .then((res) => res.json())
      .then((data) => {
        if (data.status === 'healthy') setBackendOnline(true);
      })
      .catch(() => setBackendOnline(false));

    fetch('/api/graphs')
      .then((res) => res.json())
      .then((data) => {
        setGraphs(data);
        if (data.length > 0) {
          setSelectedGraphId(data[0].graph_id);
        }
      })
      .catch((err) => console.error('Failed to load graphs:', err));
  }, []);

  // 2. Fetch Graph Details when selectedGraphId changes
  useEffect(() => {
    if (!selectedGraphId) return;

    fetch(`/api/graphs/${selectedGraphId}`)
      .then((res) => res.json())
      .then((data) => {
        setGraphData(data);
        setSelectedNode(null);
        setPredictionResult(null);
        setDefenseResult(null);
        setRecommendations([]);
      })
      .catch((err) => console.error('Error fetching graph detail:', err));
  }, [selectedGraphId]);

  // 3. Trigger Attack Path Prediction
  const handleTriggerPredict = async () => {
    if (!selectedGraphId) return;
    setIsPredicting(true);

    try {
      const res = await fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          graph_id: selectedGraphId,
          model_type: selectedModel,
          top_k: 3,
        }),
      });
      const data = await res.json();
      setPredictionResult(data);
      setActivePathIndex(0);

      // Also trigger top defense recommendations
      fetch('/api/defense/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          graph_id: selectedGraphId,
          top_n: 3,
        }),
      })
        .then((r) => r.json())
        .then((recs) => setRecommendations(recs))
        .catch((e) => console.error('Error fetching recommendations:', e));
    } catch (err) {
      console.error('Error during path prediction:', err);
    } finally {
      setIsPredicting(false);
    }
  };

  // 4. Trigger Explainability Attribution
  const handleOpenExplainability = async () => {
    if (!predictionResult || !predictionResult.paths) return;
    const currentPath = predictionResult.paths[activePathIndex];
    if (!currentPath) return;

    try {
      const res = await fetch('/api/explain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          graph_id: selectedGraphId,
          path_nodes: currentPath.nodes,
        }),
      });
      const data = await res.json();
      setExplainResult(data);
      setIsExplainModalOpen(true);
    } catch (err) {
      console.error('Error fetching explainability:', err);
    }
  };

  // 5. Simulate Patching a Vulnerability
  const handleSimulatePatch = async (nodeIndex) => {
    try {
      const res = await fetch('/api/defense/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          graph_id: selectedGraphId,
          action_type: 'patch',
          target_node_idx: nodeIndex,
        }),
      });
      const data = await res.json();
      setDefenseResult(data);
    } catch (err) {
      console.error('Error simulating patch:', err);
    }
  };

  // 6. Apply Mitigation from Recommendations
  const handleApplyRecommendation = (rec) => {
    setDefenseResult(rec);
  };

  // 7. Synthesize New Graph Scenario
  const handleGenerateGraph = async (payload) => {
    try {
      const res = await fetch('/api/graphs/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      setGraphs((prev) => [
        {
          graph_id: data.graph_id,
          num_nodes: data.num_nodes,
          num_edges: data.num_edges,
          num_vulnerable_nodes: data.nodes.filter((n) => n.is_vulnerable).length,
          num_high_value_nodes: data.nodes.filter((n) => n.is_high_value).length,
        },
        ...prev,
      ]);
      setSelectedGraphId(data.graph_id);
    } catch (err) {
      console.error('Error generating graph:', err);
    }
  };

  const activePath = predictionResult && predictionResult.paths ? predictionResult.paths[activePathIndex] : null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', width: '100vw', height: '100vh', background: 'var(--bg-main)', overflow: 'hidden' }}>
      {/* Top Cyber Command Center Navbar */}
      <Navbar
        selectedGraphId={selectedGraphId}
        graphs={graphs}
        onSelectGraph={setSelectedGraphId}
        onOpenGenerateModal={() => setIsGenerateModalOpen(true)}
        onOpenExperimentsModal={() => setIsExperimentsModalOpen(true)}
        selectedModel={selectedModel}
        onSelectModel={setSelectedModel}
        isPredicting={isPredicting}
        onTriggerPredict={handleTriggerPredict}
        backendOnline={backendOnline}
      />

      {/* Main Operations Grid Layout */}
      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '320px 1fr 340px', gap: '14px', margin: '0 16px 14px 16px', overflow: 'hidden' }}>
        {/* Left Column: Attack Path Simulator */}
        <div style={{ height: '100%', overflow: 'hidden' }}>
          <AttackPredictionPanel
            predictionResult={predictionResult}
            activePathIndex={activePathIndex}
            onSelectPathIndex={setActivePathIndex}
            onOpenExplainability={handleOpenExplainability}
          />
        </div>

        {/* Center Column: Interactive Cytoscape Graph Canvas */}
        <div className="glass-panel" style={{ height: '100%', overflow: 'hidden' }}>
          <NetworkGraphView
            graphData={graphData}
            activeAttackPath={activePath}
            mitigatedAttackPath={defenseResult?.mitigated_path}
            onSelectNode={setSelectedNode}
            selectedNodeId={selectedNode ? selectedNode.id : null}
          />
        </div>

        {/* Right Column: Split into Node Inspector (Top) and Counterfactual Defense (Bottom) */}
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: '14px', overflow: 'hidden' }}>
          <div style={{ flex: '1 1 50%', minHeight: 0 }}>
            <InspectorPanel
              selectedNode={selectedNode}
              onSimulatePatch={handleSimulatePatch}
            />
          </div>
          <div style={{ flex: '1 1 50%', minHeight: 0 }}>
            <DefenseSimulatorPanel
              defenseResult={defenseResult}
              recommendations={recommendations}
              onApplyRecommendation={handleApplyRecommendation}
            />
          </div>
        </div>
      </div>

      {/* Modals */}
      <ScenarioModal
        isOpen={isGenerateModalOpen}
        onClose={() => setIsGenerateModalOpen(false)}
        onGenerate={handleGenerateGraph}
      />

      <ExperimentsModal
        isOpen={isExperimentsModalOpen}
        onClose={() => setIsExperimentsModalOpen(false)}
      />

      {isExplainModalOpen && (
        <ExplainabilityPanel
          explainResult={explainResult}
          onClose={() => setIsExplainModalOpen(false)}
        />
      )}
    </div>
  );
}
