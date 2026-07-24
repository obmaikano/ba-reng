import { useEffect, useState, useCallback, useRef } from 'react';
import {
  Button, Card, Dialog, FormGroup, HTMLTable, InputGroup, Intent,
  OverlayToaster, Spinner, Tag,
} from '@blueprintjs/core';
import { get, post, put, del } from '../api';

interface MP {
  id: number;
  name: string;
  constituency: string;
  party: string;
}

interface Mapping {
  id: number;
  normalized_title: string;
  mp_id: number;
  mp_name: string;
  constituency: string;
  party: string;
}

export default function MinistryMappingPage() {
  const [mappings, setMappings] = useState<Mapping[]>([]);
  const [mps, setMps] = useState<MP[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Mapping | null>(null);
  const [formTitle, setFormTitle] = useState('');
  const [formMpId, setFormMpId] = useState('');

  const toasterRef = useRef<OverlayToaster | null>(null);

  const toast = (message: string, intent: Intent) => {
    toasterRef.current?.show({ message, intent });
  };

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [m, p] = await Promise.all([
        get<Mapping[]>('/api/v1/admin/ministry-mappings'),
        get<MP[]>('/api/v1/admin/mps'),
      ]);
      setMappings(m);
      setMps(p);
    } catch {
      toast('Failed to load data', Intent.DANGER);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const openCreate = () => {
    setEditing(null);
    setFormTitle('');
    setFormMpId('');
    setDialogOpen(true);
  };

  const openEdit = (m: Mapping) => {
    setEditing(m);
    setFormTitle(m.normalized_title);
    setFormMpId(String(m.mp_id));
    setDialogOpen(true);
  };

  const handleSave = async () => {
    if (!formTitle.trim() || !formMpId) return;
    try {
      if (editing) {
        await put(`/api/v1/admin/ministry-mappings/${editing.id}`, {
          normalized_title: formTitle.trim(),
          mp_id: Number(formMpId),
        });
        toast('Updated', Intent.SUCCESS);
      } else {
        await post('/api/v1/admin/ministry-mappings', {
          normalized_title: formTitle.trim(),
          mp_id: Number(formMpId),
        });
        toast('Created', Intent.SUCCESS);
      }
      setDialogOpen(false);
      await loadData();
    } catch (err: unknown) {
      toast(err instanceof Error ? err.message : 'Save failed', Intent.DANGER);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await del(`/api/v1/admin/ministry-mappings/${id}`);
      toast('Deleted', Intent.SUCCESS);
      await loadData();
    } catch (err: unknown) {
      toast(err instanceof Error ? err.message : 'Delete failed', Intent.DANGER);
    }
  };

  if (loading) {
    return <Spinner />;
  }

  return (
    <div>
      <OverlayToaster ref={toasterRef} />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h2 style={{ fontFamily: 'var(--font-mono, monospace)', color: '#BDC1C9', fontSize: '1rem', margin: 0 }}>
          Ministry Mappings
        </h2>
        <Button intent={Intent.PRIMARY} onClick={openCreate}>
          Add Mapping
        </Button>
      </div>

      <Card>
        <HTMLTable bordered striped style={{ width: '100%' }}>
          <thead>
            <tr>
              <th>Normalized Title</th>
              <th>MP</th>
              <th>Constituency</th>
              <th>Party</th>
              <th style={{ width: 120 }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {mappings.length === 0 && (
              <tr><td colSpan={5} style={{ textAlign: 'center', color: '#738091' }}>No mappings</td></tr>
            )}
            {mappings.map((m) => (
              <tr key={m.id}>
                <td style={{ fontFamily: 'var(--font-mono, monospace)', fontSize: '0.85rem' }}>
                  {m.normalized_title}
                </td>
                <td>{m.mp_name}</td>
                <td style={{ color: '#738091', fontSize: '0.85rem' }}>{m.constituency}</td>
                <td><Tag minimal>{m.party}</Tag></td>
                <td>
                  <Button minimal small onClick={() => openEdit(m)} style={{ marginRight: '0.25rem' }}>
                    Edit
                  </Button>
                  <Button minimal small intent={Intent.DANGER} onClick={() => handleDelete(m.id)}>
                    Delete
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </HTMLTable>
      </Card>

      <Dialog
        isOpen={dialogOpen}
        onClose={() => setDialogOpen(false)}
        title={editing ? 'Edit Mapping' : 'Add Mapping'}
      >
        <div style={{ padding: '1rem' }}>
          <FormGroup label="Normalized Title">
            <InputGroup
              value={formTitle}
              onChange={(e) => setFormTitle(e.target.value)}
              placeholder="minister of finance"
            />
          </FormGroup>
          <FormGroup label="MP">
            <select
              value={formMpId}
              onChange={(e) => setFormMpId(e.target.value)}
              style={{
                width: '100%', padding: '0.5rem', background: '#1F242E',
                color: '#BDC1C9', border: '1px solid #2A313D', borderRadius: 0,
              }}
            >
              <option value="">Select MP...</option>
              {mps.map((mp) => (
                <option key={mp.id} value={mp.id}>
                  {mp.name} — {mp.constituency} ({mp.party})
                </option>
              ))}
            </select>
          </FormGroup>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '1rem' }}>
            <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
            <Button intent={Intent.PRIMARY} onClick={handleSave}>
              {editing ? 'Update' : 'Create'}
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
