import React, { useEffect, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
import {
  Maximize2,
  ZoomIn,
  ZoomOut,
  Target,
  Activity,
  Grid,
  GitBranch,
} from 'lucide-react';

export default function NetworkGraphView({
  graphData,
  activeAttackPath,
  mitigatedAttackPath,
  onSelectNode,
  selectedNodeId,
}) {
  const cyRef = useRef(null);
  const containerRef = useRef(null);
  const [layoutName, setLayoutName] = useState('tiered');
  const [hoveredNode, setHoveredNode] = useState(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  // Initialize and update Cytoscape instance
  useEffect(() => {
    if (!containerRef.current || !graphData) return;

    // Convert nodes to Cytoscape format
    const cyNodes = graphData.nodes.map((n) => {
      let nodeColor = '#334155';
      let borderColor = '#475569';
      let nodeShape = 'ellipse';
      let tierLevel = 3;
      let nodeSize = 32;

      const lowerName = n.name.toLowerCase();
      const isDC = n.entity_type === 'DomainController' || lowerName.includes('dc') || lowerName.includes('domain');
      const isServer = n.entity_type === 'Server' || lowerName.includes('server') || lowerName.includes('database') || lowerName.includes('sql') || lowerName.includes('web') || lowerName.includes('share') || lowerName.includes('payment') || lowerName.includes('auth');
      const isWorkstation = n.entity_type === 'Computer' || lowerName.includes('workstation') || lowerName.includes('laptop') || lowerName.includes('pc');
      const isUser = n.entity_type === 'User';

      let deptName = 'Enterprise Network';
      let deptTag = '';

      if (isDC) {
        nodeShape = 'hexagon';
        nodeColor = '#7C3AED'; // Purple Domain Controller
        borderColor = '#C4B5FD';
        tierLevel = 1;
        nodeSize = 44;
        deptName = 'Active Directory Identity Core';
        deptTag = 'DC';
      } else if (isServer) {
        nodeShape = 'round-rectangle';
        nodeColor = '#0284C7'; // Blue Production Server
        borderColor = '#38BDF8';
        tierLevel = 2;
        nodeSize = 38;
        deptName = 'Production Server Tier';
        deptTag = 'Server';
      } else if (isWorkstation) {
        nodeShape = 'rectangle';
        tierLevel = 4;
        nodeSize = 32;

        if (lowerName.includes('hr')) {
          deptName = 'Human Resources (HR)';
          deptTag = 'HR';
          nodeColor = '#059669'; // Emerald
          borderColor = '#34D399';
        } else if (lowerName.includes('finance')) {
          deptName = 'Finance & Accounting';
          deptTag = 'Finance';
          nodeColor = '#D97706'; // Amber Gold
          borderColor = '#FBBF24';
        } else if (lowerName.includes('engineering') || lowerName.includes('dev')) {
          deptName = 'Engineering & DevOps';
          deptTag = 'Dev';
          nodeColor = '#2563EB'; // Royal Blue
          borderColor = '#60A5FA';
        } else if (lowerName.includes('exec') || lowerName.includes('leadership')) {
          deptName = 'Executive Leadership';
          deptTag = 'Exec';
          nodeColor = '#9333EA'; // Purple
          borderColor = '#C084FC';
        } else if (lowerName.includes('sales') || lowerName.includes('marketing')) {
          deptName = 'Sales & Marketing';
          deptTag = 'Sales';
          nodeColor = '#DB2777'; // Pink
          borderColor = '#F472B6';
        } else {
          deptName = 'Corporate Workstations';
          deptTag = 'Corp';
          nodeColor = '#475569';
          borderColor = '#64748B';
        }
      } else if (isUser) {
        nodeShape = 'ellipse';
        nodeColor = '#0D9488'; // Teal
        borderColor = '#2DD4BF';
        tierLevel = 5;
        nodeSize = 26;
        deptName = 'Corporate Identity';
        deptTag = 'User';
      }

      if (n.is_owned) {
        nodeColor = '#06B6D4'; // Cyan Initial Breach Foothold
        borderColor = '#67E8F9';
        nodeSize = Math.max(nodeSize, 38);
      }
      if (n.is_vulnerable) {
        borderColor = '#F59E0B'; // Amber CVE
      }
      if (n.is_target || n.is_high_value) {
        nodeColor = '#E11D48'; // Rose Crown Jewel Target
        borderColor = '#FDA4AF';
        nodeSize = Math.max(nodeSize, 44);
      }

      // Crisp Human-Readable Short Canvas Labels
      let displayName = n.name;
      if (displayName.includes('-Workstation-')) {
        const parts = displayName.split('-Workstation-');
        displayName = `[${parts[0]}] WS-${parts[1]}`;
      } else if (displayName.includes('Corporate-Web-Portal')) {
        displayName = '🌐 Web-Portal';
      } else if (displayName.includes('Customer-SQL-Database')) {
        displayName = '🗄️ SQL-DB';
      } else if (displayName.includes('Primary-Domain-Controller')) {
        displayName = '👑 Primary-DC';
      } else if (displayName.includes('Backup-DC-Enterprise')) {
        displayName = '🛡️ Backup-DC';
      } else if (displayName.includes('Payroll-DB-Server')) {
        displayName = '💰 Payroll-DB';
      } else if (displayName.includes('Payment-Gateway-Host')) {
        displayName = '💳 Payment-Host';
      } else if (displayName.includes('Internal-File-Share')) {
        displayName = '📁 File-Share';
      } else if (displayName.includes('VPN-Auth-Proxy')) {
        displayName = '🔒 VPN-Proxy';
      } else if (displayName.length > 20) {
        displayName = displayName.substring(0, 18) + '...';
      }

      return {
        data: {
          id: n.id,
          label: displayName,
          fullLabel: n.name,
          department: deptName,
          deptTag: deptTag,
          index: n.index,
          entity_type: n.entity_type,
          is_vulnerable: n.is_vulnerable,
          is_high_value: n.is_high_value,
          is_owned: n.is_owned,
          is_target: n.is_target,
          rawNode: { ...n, department: deptName },
          color: nodeColor,
          borderColor: borderColor,
          shape: nodeShape,
          size: nodeSize,
          tierLevel: tierLevel,
        },
      };
    });

    // Convert edges to Cytoscape format
    const cyEdges = graphData.edges.map((e) => {
      let edgeColor = '#22222E';
      let lineStyle = 'solid';
      let edgeWidth = 1.5;

      if (e.edge_type === 'Open') {
        edgeColor = '#F59E0B';
        lineStyle = 'dashed';
        edgeWidth = 2;
      } else if (e.edge_type === 'AdminTo') {
        edgeColor = '#EF4444';
        edgeWidth = 2;
      } else if (e.edge_type === 'CanRDP' || e.edge_type === 'ExecuteDCOM') {
        edgeColor = '#38BDF8';
        edgeWidth = 1.8;
      } else if (e.edge_type === 'MemberOf') {
        edgeColor = '#10B981';
      }

      return {
        data: {
          id: e.id,
          source: e.source,
          target: e.target,
          edge_type: e.edge_type,
          color: edgeColor,
          lineStyle: lineStyle,
          width: edgeWidth,
        },
      };
    });

    const cy = cytoscape({
      container: containerRef.current,
      elements: [...cyNodes, ...cyEdges],
      boxSelectionEnabled: false,
      autounselectify: false,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': 'data(color)',
            'label': 'data(label)',
            'color': '#FFFFFF',
            'font-size': '10px',
            'font-weight': '700',
            'font-family': 'Inter, sans-serif',
            'text-valign': 'bottom',
            'text-margin-y': 4,
            'text-background-color': 'rgba(8, 8, 12, 0.9)',
            'text-background-opacity': 0.9,
            'text-background-padding': 2,
            'text-background-shape': 'roundrectangle',
            'width': 'data(size)',
            'height': 'data(size)',
            'shape': 'data(shape)',
            'border-width': 2,
            'border-color': 'data(borderColor)',
            'transition-property': 'background-color, border-color, width, height, opacity',
            'transition-duration': '0.15s',
          },
        },
        {
          selector: 'edge',
          style: {
            'width': 'data(width)',
            'line-color': 'data(color)',
            'target-arrow-color': 'data(color)',
            'target-arrow-shape': 'triangle',
            'arrow-scale': 0.85,
            'curve-style': 'bezier',
            'line-style': 'data(lineStyle)',
            'opacity': 0.4,
            'transition-property': 'line-color, target-arrow-color, width, opacity',
            'transition-duration': '0.15s',
          },
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': 3,
            'border-color': '#FFFFFF',
            'shadow-blur': 12,
            'shadow-color': '#FFFFFF',
            'shadow-opacity': 0.6,
          },
        },
        {
          selector: '.faded',
          style: {
            'opacity': 0.12,
          },
        },
        {
          selector: '.highlighted-neighbor',
          style: {
            'opacity': 1,
            'border-width': 3,
            'border-color': '#38BDF8',
          },
        },
        {
          selector: '.highlighted-edge',
          style: {
            'opacity': 1,
            'width': 3,
            'line-color': '#38BDF8',
            'target-arrow-color': '#38BDF8',
          },
        },
        {
          selector: '.attack-path-node',
          style: {
            'border-width': 4,
            'border-color': '#F43F5E',
            'shadow-blur': 18,
            'shadow-color': '#F43F5E',
            'shadow-opacity': 0.8,
            'opacity': 1,
          },
        },
        {
          selector: '.attack-path-edge',
          style: {
            'width': 4,
            'line-color': '#F43F5E',
            'target-arrow-color': '#F43F5E',
            'opacity': 1,
            'line-style': 'solid',
            'arrow-scale': 1.2,
            'shadow-blur': 10,
            'shadow-color': '#F43F5E',
            'shadow-opacity': 0.7,
          },
        },
      ],
    });

    cyRef.current = cy;

    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      const rawNode = node.data('rawNode');
      if (onSelectNode) onSelectNode(rawNode);

      cy.elements().removeClass('faded highlighted-neighbor highlighted-edge');
      const neighborhood = node.neighborhood().add(node);
      cy.elements().difference(neighborhood).addClass('faded');
      node.neighborhood('node').addClass('highlighted-neighbor');
      node.neighborhood('edge').addClass('highlighted-edge');
    });

    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        cy.elements().removeClass('faded highlighted-neighbor highlighted-edge');
      }
    });

    cy.on('mouseover', 'node', (evt) => {
      const node = evt.target;
      const rawNode = node.data('rawNode');
      const renderedPos = node.renderedPosition();
      setHoveredNode({
        ...rawNode,
        deptLabel: node.data('department'),
      });
      setTooltipPos({ x: renderedPos.x, y: renderedPos.y });
    });

    cy.on('mouseout', 'node', () => {
      setHoveredNode(null);
    });

    applyLayout(cy, layoutName);

    return () => {
      cy.destroy();
    };
  }, [graphData]);

  const applyLayout = (cyInstance, type) => {
    if (!cyInstance) return;

    let layoutConfig = {};

    if (type === 'tiered') {
      layoutConfig = {
        name: 'breadthfirst',
        directed: true,
        padding: 30,
        spacingFactor: 1.2,
        avoidOverlap: true,
        circle: false,
        roots: cyInstance.nodes('[tierLevel = 1]'),
      };
    } else if (type === 'concentric') {
      layoutConfig = {
        name: 'concentric',
        concentric: (node) => 6 - node.data('tierLevel'),
        levelWidth: () => 1,
        padding: 30,
        avoidOverlap: true,
        spacingFactor: 1.15,
      };
    } else if (type === 'grid') {
      layoutConfig = {
        name: 'grid',
        padding: 30,
        avoidOverlap: true,
        rows: Math.ceil(Math.sqrt(cyInstance.nodes().length)),
      };
    } else {
      layoutConfig = {
        name: 'cose',
        idealEdgeLength: 60,
        nodeOverlap: 20,
        refresh: 20,
        fit: true,
        padding: 30,
        randomize: false,
        componentSpacing: 100,
        nodeRepulsion: 400000,
        edgeElasticity: 100,
        nestingFactor: 5,
        gravity: 80,
        numIter: 300,
        initialTemp: 200,
        coolingFactor: 0.95,
        minTemp: 1.0,
      };
    }

    const layout = cyInstance.layout(layoutConfig);
    layout.run();
  };

  const handleSwitchLayout = (type) => {
    setLayoutName(type);
    applyLayout(cyRef.current, type);
  };

  useEffect(() => {
    if (!cyRef.current) return;
    const cy = cyRef.current;

    cy.elements().removeClass('attack-path-node attack-path-edge');

    if (activeAttackPath && activeAttackPath.nodes) {
      activeAttackPath.nodes.forEach((nodeIdx) => {
        cy.nodes(`[index = ${nodeIdx}]`).addClass('attack-path-node');
      });

      for (let i = 0; i < activeAttackPath.nodes.length - 1; i++) {
        const u = activeAttackPath.nodes[i];
        const v = activeAttackPath.nodes[i + 1];
        cy.edges(`[source = "node_${u}"][target = "node_${v}"]`).addClass('attack-path-edge');
      }
    }
  }, [activeAttackPath]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', overflow: 'hidden' }}>
      <div ref={containerRef} id="cy-container" />

      {/* Sleek Top-Right Canvas Toolbar */}
      <div
        style={{
          position: 'absolute',
          top: '10px',
          right: '10px',
          padding: '4px',
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          background: '#0D0D14',
          border: '1px solid #22222E',
          borderRadius: '8px',
          zIndex: 10,
          boxShadow: '0 4px 15px rgba(0,0,0,0.6)',
        }}
      >
        <button
          className="btn-cyber"
          onClick={() => handleSwitchLayout('tiered')}
          style={{
            padding: '4px 8px',
            fontSize: '0.72rem',
            background: layoutName === 'tiered' ? '#FFFFFF' : '#14141E',
            color: layoutName === 'tiered' ? '#000000' : 'var(--text-secondary)',
          }}
          title="Hierarchical Tiered View (DCs → Servers → Workstations)"
        >
          <GitBranch size={12} /> Tiered
        </button>

        <button
          className="btn-cyber"
          onClick={() => handleSwitchLayout('concentric')}
          style={{
            padding: '4px 8px',
            fontSize: '0.72rem',
            background: layoutName === 'concentric' ? '#FFFFFF' : '#14141E',
            color: layoutName === 'concentric' ? '#000000' : 'var(--text-secondary)',
          }}
          title="Concentric Security Rings"
        >
          <Target size={12} /> Rings
        </button>

        <button
          className="btn-cyber"
          onClick={() => handleSwitchLayout('grid')}
          style={{
            padding: '4px 8px',
            fontSize: '0.72rem',
            background: layoutName === 'grid' ? '#FFFFFF' : '#14141E',
            color: layoutName === 'grid' ? '#000000' : 'var(--text-secondary)',
          }}
          title="Subnet Grid View"
        >
          <Grid size={12} /> Grid
        </button>

        <button
          className="btn-cyber"
          onClick={() => handleSwitchLayout('cose')}
          style={{
            padding: '4px 8px',
            fontSize: '0.72rem',
            background: layoutName === 'cose' ? '#FFFFFF' : '#14141E',
            color: layoutName === 'cose' ? '#000000' : 'var(--text-secondary)',
          }}
          title="Organic Force-Directed Spring Layout"
        >
          <Activity size={12} /> Organic
        </button>

        <div style={{ width: '1px', height: '14px', background: '#2B2B38', margin: '0 2px' }} />

        <button
          className="btn-cyber btn-outline"
          onClick={() => cyRef.current && cyRef.current.fit(null, 30)}
          style={{ padding: '4px 6px' }}
          title="Fit Canvas"
        >
          <Maximize2 size={12} />
        </button>

        <button
          className="btn-cyber btn-outline"
          onClick={() => cyRef.current && cyRef.current.zoom(cyRef.current.zoom() * 1.25)}
          style={{ padding: '4px 6px' }}
          title="Zoom In"
        >
          <ZoomIn size={12} />
        </button>

        <button
          className="btn-cyber btn-outline"
          onClick={() => cyRef.current && cyRef.current.zoom(cyRef.current.zoom() * 0.8)}
          style={{ padding: '4px 6px' }}
          title="Zoom Out"
        >
          <ZoomOut size={12} />
        </button>
      </div>

      {/* Floating Compact Department Legend */}
      <div
        style={{
          position: 'absolute',
          bottom: '10px',
          left: '10px',
          padding: '6px 10px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          background: 'rgba(11, 11, 16, 0.94)',
          border: '1px solid #1E1E28',
          borderRadius: '6px',
          fontSize: '0.68rem',
          zIndex: 10,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
          <div style={{ width: '8px', height: '8px', background: '#7C3AED', borderRadius: '2px' }} />
          <span>👑 DC</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
          <div style={{ width: '8px', height: '8px', background: '#0284C7', borderRadius: '2px' }} />
          <span>🌐 Server</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
          <div style={{ width: '8px', height: '8px', background: '#059669', borderRadius: '2px' }} />
          <span>🏢 HR</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
          <div style={{ width: '8px', height: '8px', background: '#D97706', borderRadius: '2px' }} />
          <span>💰 Finance</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
          <div style={{ width: '8px', height: '8px', background: '#2563EB', borderRadius: '2px' }} />
          <span>⚙️ Dev</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
          <div style={{ width: '8px', height: '8px', background: '#06B6D4', borderRadius: '2px' }} />
          <span>🎯 Foothold</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
          <div style={{ width: '8px', height: '8px', background: '#E11D48', borderRadius: '2px' }} />
          <span>🌸 Target</span>
        </div>
      </div>

      {/* Floating Detailed Hover Card */}
      {hoveredNode && (
        <div
          style={{
            position: 'absolute',
            left: `${Math.min(window.innerWidth - 320, tooltipPos.x + 15)}px`,
            top: `${Math.min(window.innerHeight - 170, tooltipPos.y + 15)}px`,
            padding: '10px 14px',
            background: '#0B0B10',
            border: '1px solid #333345',
            borderRadius: '8px',
            boxShadow: '0 10px 30px rgba(0,0,0,0.95)',
            zIndex: 100,
            pointerEvents: 'none',
            minWidth: '230px',
          }}
        >
          <div style={{ fontSize: '0.82rem', fontWeight: '800', color: '#FFFFFF', marginBottom: '2px' }}>
            {hoveredNode.name}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#38BDF8', fontWeight: '600', marginBottom: '4px' }}>
            🏢 {hoveredNode.deptLabel || hoveredNode.department || 'Enterprise Asset'}
          </div>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
            Type: {hoveredNode.entity_type} {hoveredNode.os ? `• ${hoveredNode.os}` : ''}
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
            {hoveredNode.is_owned && <span className="badge badge-cyan" style={{ fontSize: '0.6rem' }}>Adversary Foothold</span>}
            {hoveredNode.is_target && <span className="badge badge-rose" style={{ fontSize: '0.6rem' }}>Target Crown Jewel</span>}
            {hoveredNode.is_vulnerable && <span className="badge badge-amber" style={{ fontSize: '0.6rem' }}>Unpatched CVE Exploit</span>}
          </div>
        </div>
      )}
    </div>
  );
}
