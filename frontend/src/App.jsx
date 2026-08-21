import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import NetworkGraphView from './components/NetworkGraphView';
import AttackPredictionPanel from './components/AttackPredictionPanel';
import InspectorPanel from './components/InspectorPanel';
import DefenseSimulatorPanel from './components/DefenseSimulatorPanel';
import ExplainabilityPanel from './components/ExplainabilityPanel';
import ScenarioModal from './components/ScenarioModal';
import ExperimentsModal from './components/ExperimentsModal';
import VMInfrastructureModal from './components/VMInfrastructureModal';
import MultiHeadXAIModal from './components/MultiHeadXAIModal';
import { DEMO_STORIES } from './components/GuidedDemoBanner';
import { Server, ShieldCheck } from 'lucide-react';

export default function App() {
  // Graph State
  const [graphs, setGraphs] = useState([]);
  const [selectedGraphId, setSelectedGraphId] = useState('');
  const [graphData, setGraphData] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);

  // Scenario / Story State
  const [currentStoryId, setCurrentStoryId] = useState('phished_hr_laptop');

  // Prediction State
  const [selectedModel, setSelectedModel] = useState('gat');
  const [predictionResult, setPredictionResult] = useState(null);
  const [activePathIndex, setActivePathIndex] = useState(0);
  const [isPredicting, setIsPredicting] = useState(false);

  // Live Attack Simulation
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

  // Origin & Target Selection
  const [selectedSourceIdx, setSelectedSourceIdx] = useState(0);
  const [selectedTargetIdx, setSelectedTargetIdx] = useState(0);

  // Right Side Panel Tab: 'inspector' | 'defense'
  const [rightPanelTab, setRightPanelTab] = useState('inspector');

  // Counterfactual Defense
  const [defenseResult, setDefenseResult] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);

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
        const sIdx = data.source_idx ?? 0;
        let tIdx = data.target_idx ?? (data.nodes.length > 1 ? data.nodes.length - 1 : 0);
        if (sIdx === tIdx && data.nodes && data.nodes.length > 1) {
          tIdx = sIdx === 0 ? 1 : 0;
        }
        setSelectedSourceIdx(sIdx);
        setSelectedTargetIdx(tIdx);
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
  const handleTriggerPredict = async (customSource, customTarget) => {
    if (!selectedGraphId) return;
    setIsPredicting(true);

    const sIdx = customSource !== undefined ? customSource : selectedSourceIdx;
    const tIdx = customTarget !== undefined ? customTarget : selectedTargetIdx;

    try {
      const res = await fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          graph_id: selectedGraphId,
          model_type: selectedModel,
          source_idx: sIdx,
          target_idx: tIdx,
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
    } else {
      clearInterval(interval);
    }
    return () => clearInterval(interval);
  }, [isPlaying, timelineEvents]);

  // 5. Trigger Explainability
  const handleOpenExplainability = async () => {
    if (!selectedGraphId || !activePath) return;

    try {
      const res = await fetch('/api/explain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          graph_id: selectedGraphId,
          path_nodes: activePath.nodes,
        }),
      });
      const data = await res.json();
      setExplainResult(data);
      setIsExplainModalOpen(true);
    } catch (err) {
      console.error('Error fetching XAI explanation:', err);
    }
  };

  // 6. Trigger Advanced Multi-Head XAI
  const handleOpenAdvancedXAI = async (sourceIdx, targetIdx) => {
    if (!selectedGraphId) return;

    try {
      const res = await fetch('/api/xai/multi_head_attention', {
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
      console.error('Error fetching advanced multi-head XAI:', err);
    }
  };

  // 7. Simulate Patch Defense
  const handleSimulatePatch = async (nodeIdx) => {
    if (!selectedGraphId) return;

    try {
      const res = await fetch('/api/defense/simulate_patch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          graph_id: selectedGraphId,
          node_idx: nodeIdx,
        }),
      });
      const data = await res.json();
      setDefenseResult(data);
      setRightPanelTab('defense');
    } catch (err) {
      console.error('Error simulating patch defense:', err);
    }
  };

  // 8. Generate Synthetic Graph
  const handleGenerateGraph = async (config) => {
    setIsGenerating(true);
    try {
      const res = await fetch('/api/graphs/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
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
        ...prev.filter((g) => g.graph_id !== data.graph_id),
      ]);
      setSelectedGraphId(data.graph_id);
      setGraphData(data);

      const sIdx = data.source_idx ?? 0;
      const tIdx = data.target_idx ?? (data.nodes.length > 1 ? data.nodes.length - 1 : 0);
      setSelectedSourceIdx(sIdx);
      setSelectedTargetIdx(tIdx);
      setSelectedNode(null);
      setPredictionResult(null);
      setDefenseResult(null);
      setRecommendations([]);
      setTimelineEvents([]);
      setCurrentStepIndex(0);
      setIsPlaying(false);
    } catch (err) {
      console.error('Error generating graph:', err);
    } finally {
      setIsGenerating(false);
    }
  };

  // Guided Demo Scenario Selector Handler
  const handleSelectStory = (storyId) => {
    setCurrentStoryId(storyId);
    if (!graphData || !graphData.nodes) return;
    const story = DEMO_STORIES.find((s) => s.id === storyId);
    if (!story) return;

    const startNode = graphData.nodes.find((n) => n.name.toLowerCase().includes(story.startNodeName.toLowerCase().split('-')[0])) || graphData.nodes[0];
    const targetNode = graphData.nodes.find((n) => n.name.toLowerCase().includes(story.targetNodeName.toLowerCase().split('-')[0])) || graphData.nodes[graphData.nodes.length - 1];

    if (startNode) setSelectedSourceIdx(startNode.index);
    if (targetNode) setSelectedTargetIdx(targetNode.index);

    handleTriggerPredict(startNode?.index, targetNode?.index);
  };

  // Active path to highlight on Cytoscape canvas
  const activePath = predictionResult && predictionResult.paths ? predictionResult.paths[activePathIndex] : null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', width: '100vw', height: '100vh', background: '#050508', overflow: 'hidden' }}>
      {/* Top Navbar */}
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
        onTriggerPredict={() => handleTriggerPredict()}
        backendOnline={backendOnline}
        currentStoryId={currentStoryId}
        onSelectStory={handleSelectStory}
        onQuickGenerateNodes={(count) => {
          const randSuffix = Math.floor(Math.random() * 9000 + 1000);
          handleGenerateGraph({
            scenario_name: `syn_enterprise_${count}n_${randSuffix}`,
            target_nodes: count,
            edge_multiplier: 2.2,
            cve_probability: 0.25,
            spn_probability: 0.35,
          });
        }}
        isGenerating={isGenerating}
      />

      {/* Main Command Center Layout */}
      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '310px 1fr 330px', gap: '10px', margin: '0 14px 10px 14px', overflow: 'hidden' }}>
        {/* Left Column: Attack Simulator & Playback */}
        <div style={{ height: '100%', overflow: 'hidden' }}>
          <AttackPredictionPanel
            graphData={graphData}
            selectedSourceIdx={selectedSourceIdx}
            onSelectSourceIdx={(idx) => {
              setSelectedSourceIdx(idx);
              handleTriggerPredict(idx, selectedTargetIdx);
            }}
            selectedTargetIdx={selectedTargetIdx}
            onSelectTargetIdx={(idx) => {
              setSelectedTargetIdx(idx);
              handleTriggerPredict(selectedSourceIdx, idx);
            }}
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
            isPredicting={isPredicting}
            onTriggerPredict={handleTriggerPredict}
          />
        </div>

        {/* Center Column: Full-Height Interactive Canvas */}
        <div style={{ height: '100%', overflow: 'hidden', background: '#08080C', border: '1px solid #1A1A24', borderRadius: '10px' }}>
          <NetworkGraphView
            graphData={graphData}
            activeAttackPath={activePath}
            defenseResult={defenseResult}
            onClearDefense={() => setDefenseResult(null)}
            onSelectNode={(node) => {
              setSelectedNode(node);
              setRightPanelTab('inspector');
            }}
            selectedNodeId={selectedNode ? selectedNode.id : null}
          />
        </div>

        {/* Right Column: Full-Height Tabbed Posture & Decision Center */}
        <div
          style={{
            height: '100%',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            background: '#0B0B10',
            border: '1px solid #1E1E28',
            borderRadius: '10px',
          }}
        >
          {/* Tab Switcher Header */}
          <div style={{ display: 'flex', background: '#0E0E16', borderBottom: '1px solid #1E1E28', padding: '3px' }}>
            <button
              onClick={() => setRightPanelTab('inspector')}
              style={{
                flex: 1,
                padding: '7px 10px',
                fontSize: '0.74rem',
                fontWeight: '700',
                borderRadius: '6px',
                border: 'none',
                background: rightPanelTab === 'inspector' ? '#FFFFFF' : 'transparent',
                color: rightPanelTab === 'inspector' ? '#000000' : 'var(--text-secondary)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '5px',
              }}
            >
              <Server size={13} /> Asset Posture
            </button>

            <button
              onClick={() => setRightPanelTab('defense')}
              style={{
                flex: 1,
                padding: '7px 10px',
                fontSize: '0.74rem',
                fontWeight: '700',
                borderRadius: '6px',
                border: 'none',
                background: rightPanelTab === 'defense' ? '#FFFFFF' : 'transparent',
                color: rightPanelTab === 'defense' ? '#000000' : 'var(--text-secondary)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '5px',
              }}
            >
              <ShieldCheck size={13} /> Defenses
            </button>
          </div>

          {/* Full-Height Tab Content */}
          <div style={{ flex: 1, overflowY: 'auto' }}>
            {rightPanelTab === 'inspector' ? (
              <InspectorPanel
                selectedNode={selectedNode}
                onSimulatePatch={handleSimulatePatch}
                onSetSource={(idx) => {
                  setSelectedSourceIdx(idx);
                  handleTriggerPredict(idx, selectedTargetIdx);
                }}
                onSetTarget={(idx) => {
                  setSelectedTargetIdx(idx);
                  handleTriggerPredict(selectedSourceIdx, idx);
                }}
              />
            ) : (
              <DefenseSimulatorPanel
                defenseResult={defenseResult}
                recommendations={recommendations}
                onApplyRecommendation={(rec) => setDefenseResult(rec)}
              />
            )}
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
