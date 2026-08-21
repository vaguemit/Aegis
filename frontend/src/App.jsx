import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import NetworkGraphView from './components/NetworkGraphView';
import InspectorPanel from './components/InspectorPanel';
import AttackPredictionPanel from './components/AttackPredictionPanel';
import ExplainabilityPanel from './components/ExplainabilityPanel';
import DefenseSimulatorPanel from './components/DefenseSimulatorPanel';
import ScenarioModal from './components/ScenarioModal';
import ExperimentsModal from './components/ExperimentsModal';
import VMInfrastructureModal from './components/VMInfrastructureModal';
import MultiHeadXAIModal from './components/MultiHeadXAIModal';

export default function App() {
  const [graphs, setGraphs] = useState([]);
  const [selectedGraphId, setSelectedGraphId] = useState('');
  const [graphData, setGraphData] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [selectedModel, setSelectedModel] = useState('gat');

  const [isPredicting, setIsPredicting] = useState(false);
  const [predictionResult, setPredictionResult] = useState(null);
  const [activePathIndex, setActivePathIndex] = useState(0);

  // Live Attack Step Player State
  const [timelineEvents, setTimelineEvents] = useState([]);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  // Modals
  const [explainResult, setExplainResult] = useState(null);
  const [isExplainModalOpen, setIsExplainModalOpen] = useState(false);

  const [advancedXaiData, setAdvancedXaiData] = useState(null);
  const [isAdvancedXaiOpen, setIsAdvancedXaiOpen] = useState(false);

  const [isVmModalOpen, setIsVmModalOpen] = useState(false);
  const [isGenerateModalOpen, setIsGenerateModalOpen] = useState(false);
  const [isExperimentsModalOpen, setIsExperimentsModalOpen] = useState(false);

  // Counterfactual Defense
  const [defenseResult, setDefenseResult] = useState(null);
  const [recommendations, setRecommendations] = useState([]);

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
        setTimelineEvents([]);
        setCurrentStepIndex(0);
        setIsPlaying(false);
      })
      .catch((err) => console.error('Error fetching graph detail:', err));
  }, [selectedGraphId]);

  // 3. Trigger Attack Path Prediction & Live Timeline
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

      // Trigger live attack timeline simulation
      const topPathNodes = data.paths && data.paths.length > 0 ? data.paths[0].nodes : null;
      fetch('/api/simulation/play', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          graph_id: selectedGraphId,
          path_nodes: topPathNodes,
        }),
      })
        .then((r) => r.json())
        .then((playData) => {
          setTimelineEvents(playData.timeline || []);
          setCurrentStepIndex(0);
        })
        .catch((e) => console.error('Error fetching timeline:', e));

      // Trigger top defense recommendations
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

  // 4. Live Attack Player Ticker
  useEffect(() => {
    let interval = null;
    if (isPlaying && timelineEvents.length > 0) {
      interval = setInterval(() => {
        setCurrentStepIndex((prev) => {
          if (prev >= timelineEvents.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 1500);
    }
    return () => clearInterval(interval);
  }, [isPlaying, timelineEvents]);

  // 5. Trigger Explainability Attribution
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

  // 6. Trigger Advanced Multi-Head XAI for specific edge
  const handleOpenAdvancedXAI = async (sourceIdx, targetIdx) => {
    try {
      const res = await fetch('/api/xai/decompose', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          graph_id: selectedGraphId,
          source_idx: sourceIdx,
          target_idx: targetIdx,
        }),
      });
      const data = await res.json();
      setAdvancedXaiData(data);
      setIsAdvancedXaiOpen(true);
    } catch (err) {
      console.error('Error decomposing multi-head XAI:', err);
    }
  };

  // 7. Simulate Patching a Vulnerability
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

  // 8. Synthesize New Graph Scenario
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

  // Active path to highlight on Cytoscape canvas
  const activePath = predictionResult && predictionResult.paths ? predictionResult.paths[activePathIndex] : null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', width: '100vw', height: '100vh', background: 'var(--bg-pitch-black)', overflow: 'hidden' }}>
      {/* Top Obsidian Navbar */}
      <Navbar
        selectedGraphId={selectedGraphId}
        graphs={graphs}
        onSelectGraph={setSelectedGraphId}
        onOpenGenerateModal={() => setIsGenerateModalOpen(true)}
        onOpenExperimentsModal={() => setIsExperimentsModalOpen(true)}
        onOpenVmModal={() => setIsVmModalOpen(true)}
        selectedModel={selectedModel}
        onSelectModel={setSelectedModel}
        isPredicting={isPredicting}
        onTriggerPredict={handleTriggerPredict}
        backendOnline={backendOnline}
      />

      {/* Main Command Center Layout */}
      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '330px 1fr 340px', gap: '12px', margin: '0 14px 12px 14px', overflow: 'hidden' }}>
        {/* Left Column: Attack Path Simulator & Live Player */}
        <div style={{ height: '100%', overflow: 'hidden' }}>
          <AttackPredictionPanel
            predictionResult={predictionResult}
            activePathIndex={activePathIndex}
            onSelectPathIndex={setActivePathIndex}
            onOpenExplainability={handleOpenExplainability}
            onOpenAdvancedXAI={handleOpenAdvancedXAI}
            timelineEvents={timelineEvents}
            currentStepIndex={currentStepIndex}
            onStepChange={setCurrentStepIndex}
            isPlaying={isPlaying}
            onTogglePlay={() => setIsPlaying(!isPlaying)}
            onReset={() => { setCurrentStepIndex(0); setIsPlaying(false); }}
          />
        </div>

        {/* Center Column: Interactive Cytoscape Graph Canvas */}
        <div className="glass-panel" style={{ height: '100%', overflow: 'hidden', background: '#07070A', border: '1px solid #1E1E28' }}>
          <NetworkGraphView
            graphData={graphData}
            activeAttackPath={activePath}
            mitigatedAttackPath={defenseResult?.mitigated_path}
            onSelectNode={setSelectedNode}
            selectedNodeId={selectedNode ? selectedNode.id : null}
          />
        </div>

        {/* Right Column: Node/VM Inspector (Top) and Counterfactual Defense (Bottom) */}
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: '12px', overflow: 'hidden' }}>
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
              onApplyRecommendation={(rec) => setDefenseResult(rec)}
            />
          </div>
        </div>
      </div>

      {/* Modals */}
      <VMInfrastructureModal
        isOpen={isVmModalOpen}
        onClose={() => setIsVmModalOpen(false)}
        graphId={selectedGraphId}
      />

      <MultiHeadXAIModal
        isOpen={isAdvancedXaiOpen}
        onClose={() => setIsAdvancedXaiOpen(false)}
        xaiData={advancedXaiData}
      />

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
