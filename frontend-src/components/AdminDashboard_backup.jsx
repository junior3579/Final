import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { 
  Users, 
  Home, 
  Trophy, 
  UserPlus, 
  Edit, 
  Trash2, 
  Key,
  Coins,
  MessageCircle,
  FolderPlus,
  Swords,
  Save,
  PlusCircle,
  Settings
} from 'lucide-react'
import OnlineUsers from './OnlineUsers'

const AdminDashboard = ({ user }) => {
  const [usuarios, setUsuarios] = useState([])
  const [salas, setSalas] = useState([])
  const [categorias, setCategorias] = useState([])
  const [torneios, setTorneios] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // Estados para formulários
  const [novoUsuario, setNovoUsuario] = useState({ nome: '', senha: '', pontos: '', whatsapp: '', pix_tipo: '', pix_chave: '' })
  const [usuarioEditando, setUsuarioEditando] = useState(null)
  const [novaCategoria, setNovaCategoria] = useState('')
  const [novoTorneio, setNovoTorneio] = useState('')
  const [buscaParticipante, setBuscaParticipante] = useState({ torneioId: '', valor: '' })

  useEffect(() => {
    carregarDados()
  }, [])

  const carregarDados = async () => {
    try {
      const [usuariosRes, salasRes, categoriasRes, torneiosRes] = await Promise.all([
        fetch('/api/usuarios'),
        fetch('/api/salas'),
        fetch('/api/categorias'),
        fetch('/api/torneios')
      ])
      setUsuarios(await usuariosRes.json())
      setSalas(await salasRes.json())
      setCategorias(await categoriasRes.json())
      setTorneios(await torneiosRes.json())
    } catch (err) { setError('Erro ao carregar dados') }
  }

  const cadastrarUsuario = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setSuccess('')
    try {
      const res = await fetch('/api/usuarios', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(novoUsuario),
      })
      const data = await res.json()
      if (res.ok) {
        setSuccess(data.message)
        setNovoUsuario({ nome: '', senha: '', pontos: '', whatsapp: '', pix_tipo: '', pix_chave: '' })
        carregarDados()
      } else setError(data.error)
    } catch (err) { setError('Erro de conexão') }
    finally { setLoading(false) }
  }

  const salvarEdicaoUsuario = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setSuccess('')
    try {
      const res = await fetch(`/api/usuarios/${usuarioEditando.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(usuarioEditando),
      })
      if (res.ok) {
        setSuccess('Usuário atualizado!')
        setUsuarioEditando(null)
        carregarDados()
      } else {
        const data = await res.json()
        setError(data.error)
      }
    } catch (err) { setError('Erro ao salvar') }
    finally { setLoading(false) }
  }

  const adicionarParticipanteManual = async (torneioId) => {
    if (!buscaParticipante.valor) return
    try {
      const res = await fetch(`/api/torneios/${torneioId}/inscrever`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nome_usuario: buscaParticipante.valor }),
      })
      const data = await res.json()
      if (res.ok) {
        setSuccess('Participante adicionado!')
        setBuscaParticipante({ torneioId: '', valor: '' })
        carregarDados()
      } else setError(data.error)
    } catch (err) { setError('Erro ao adicionar') }
  }

  const removerUsuario = async (id) => {
    if (!confirm('Tem certeza?')) return
    await fetch(`/api/usuarios/${id}`, { method: 'DELETE' })
    carregarDados()
  }

  const criarCategoria = async (e) => {
    e.preventDefault()
    await fetch('/api/categorias', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nome: novaCategoria }),
    })
    setNovaCategoria('')
    carregarDados()
  }

  const removerCategoria = async (id) => {
    if (!confirm('Remover categoria?')) return
    await fetch(`/api/categorias/${id}`, { method: 'DELETE' })
    carregarDados()
  }

  const criarTorneio = async (e) => {
    e.preventDefault()
    await fetch('/api/torneios', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nome: novoTorneio }),
    })
    setNovoTorneio('')
    carregarDados()
  }

  const eliminarParticipante = async (torneioId, usuarioId) => {
    await fetch(`/api/torneios/${torneioId}/eliminar`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ usuario_id: usuarioId }),
    })
    carregarDados()
  }

  return (
    <div className="space-y-6">
      <OnlineUsers />
      {error && <Alert className="bg-red-50 border-red-200"><AlertDescription className="text-red-600">{error}</AlertDescription></Alert>}
      {success && <Alert className="bg-green-50 border-green-200"><AlertDescription className="text-green-600">{success}</AlertDescription></Alert>}

      <Tabs defaultValue="usuarios" className="w-full">
        <TabsList className="grid w-full grid-cols-5 bg-gray-100 p-1 rounded-lg">
          <TabsTrigger value="usuarios"><Users className="h-4 w-4 mr-2" />Usuários</TabsTrigger>
          <TabsTrigger value="salas"><Home className="h-4 w-4 mr-2" />Salas</TabsTrigger>
          <TabsTrigger value="categorias"><FolderPlus className="h-4 w-4 mr-2" />Categorias</TabsTrigger>
          <TabsTrigger value="torneios"><Swords className="h-4 w-4 mr-2" />Torneios</TabsTrigger>
          <TabsTrigger value="gerenciar"><Settings className="h-4 w-4 mr-2" />Gerenciar</TabsTrigger>
        </TabsList>

        <TabsContent value="usuarios" className="space-y-4">
          {usuarios.map(u => (
            <Card key={u.id} className="p-4">
              <div className="flex justify-between items-center">
                <div>
                  <span className="font-bold">{u.nome}</span> <Badge>{u.pontos} pts</Badge>
                  <div className="text-xs text-gray-500">Pix: {u.pix_tipo || 'N/A'} - {u.pix_chave || 'N/A'}</div>
                  <div className="text-xs text-gray-400">Senha: {u.senha}</div>
                </div>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" onClick={() => setUsuarioEditando(u)}><Edit className="h-4 w-4" /></Button>
                  <Button variant="destructive" size="sm" onClick={() => removerUsuario(u.id)}><Trash2 className="h-4 w-4" /></Button>
                </div>
              </div>
              {usuarioEditando?.id === u.id && (
                <form onSubmit={salvarEdicaoUsuario} className="mt-4 space-y-2 border-t pt-4">
                  <div className="grid grid-cols-2 gap-2">
                    <div className="space-y-1">
                      <Label className="text-xs">Nome</Label>
                      <Input value={usuarioEditando.nome} onChange={e => setUsuarioEditando({...usuarioEditando, nome: e.target.value})} />
                    </div>
                    <div className="space-y-1">
                      <Label className="text-xs">Senha</Label>
                      <Input value={usuarioEditando.senha} onChange={e => setUsuarioEditando({...usuarioEditando, senha: e.target.value})} />
                    </div>
                    <div className="space-y-1">
                      <Label className="text-xs">Pontos</Label>
                      <Input type="number" value={usuarioEditando.pontos} onChange={e => setUsuarioEditando({...usuarioEditando, pontos: e.target.value})} />
                    </div>
                    <div className="space-y-1">
                      <Label className="text-xs">WhatsApp</Label>
                      <Input value={usuarioEditando.whatsapp} onChange={e => setUsuarioEditando({...usuarioEditando, whatsapp: e.target.value})} />
                    </div>
                    <div className="space-y-1">
                      <Label className="text-xs">Tipo Pix</Label>
                      <Input value={usuarioEditando.pix_tipo} onChange={e => setUsuarioEditando({...usuarioEditando, pix_tipo: e.target.value})} />
                    </div>
                    <div className="space-y-1">
                      <Label className="text-xs">Chave Pix</Label>
                      <Input value={usuarioEditando.pix_chave} onChange={e => setUsuarioEditando({...usuarioEditando, pix_chave: e.target.value})} />
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button type="submit" size="sm" className="w-full"><Save className="h-4 w-4 mr-2" />Salvar Alterações</Button>
                    <Button type="button" variant="ghost" size="sm" onClick={() => setUsuarioEditando(null)}>Cancelar</Button>
                  </div>
                </form>
              )}
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="categorias" className="space-y-4">
          <Card className="p-4">
            <form onSubmit={criarCategoria} className="flex gap-2">
              <Input value={novaCategoria} onChange={e => setNovaCategoria(e.target.value)} placeholder="Nova Categoria" />
              <Button type="submit">Adicionar</Button>
            </form>
          </Card>
          {categorias.map(c => (
            <Card key={c.id} className="p-4 flex justify-between items-center">
              <span>{c.nome} <Badge variant="secondary">{c.total_salas} salas</Badge></span>
              <Button variant="destructive" size="sm" onClick={() => removerCategoria(c.id)}><Trash2 className="h-4 w-4" /></Button>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="torneios" className="space-y-4">
          <Card className="p-4">
            <form onSubmit={criarTorneio} className="flex gap-2">
              <Input value={novoTorneio} onChange={e => setNovoTorneio(e.target.value)} placeholder="Nome do Torneio" />
              <Button type="submit">Criar Torneio</Button>
            </form>
          </Card>
          {torneios.map(t => (
            <Card key={t.id} className="p-4 space-y-2">
              <div className="flex justify-between">
                <h3 className="font-bold">{t.nome} - <Badge>{t.status}</Badge></h3>
                {t.status === 'inscricao' && (
                  <div className="flex gap-2">
                    <Input 
                      size="sm" 
                      placeholder="Nome ou ID" 
                      value={buscaParticipante.torneioId === t.id ? buscaParticipante.valor : ''}
                      onChange={e => setBuscaParticipante({ torneioId: t.id, valor: e.target.value })}
                    />
                    <Button size="sm" onClick={() => adicionarParticipanteManual(t.id)}><PlusCircle className="h-4 w-4" /></Button>
                    <Button size="sm" onClick={() => {
                      fetch(`/api/torneios/${t.id}/iniciar`, { method: 'POST' }).then(() => carregarDados())
                    }}>Iniciar</Button>
                  </div>
                )}
              </div>
              <div className="grid grid-cols-2 gap-2">
                {t.participantes.map(p => (
                  <div key={p.id} className="flex justify-between items-center bg-gray-50 p-2 rounded">
                    <span className={p.status === 'eliminado' ? 'line-through text-gray-400' : ''}>{p.nome}</span>
                    {t.status === 'em_andamento' && p.status === 'ativo' && (
                      <Button size="xs" variant="outline" onClick={() => eliminarParticipante(t.id, p.id)}>Eliminar</Button>
                    )}
                  </div>
                ))}
              </div>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="gerenciar" className="space-y-4">
           <Card className="p-4">
              <CardTitle>Cadastrar Novo Usuário</CardTitle>
              <form onSubmit={cadastrarUsuario} className="space-y-4 mt-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <Label>Nome de Usuário</Label>
                    <Input value={novoUsuario.nome} onChange={e => setNovoUsuario({...novoUsuario, nome: e.target.value})} placeholder="Ex: joao123" required />
                  </div>
                  <div className="space-y-1">
                    <Label>Senha</Label>
                    <Input type="text" value={novoUsuario.senha} onChange={e => setNovoUsuario({...novoUsuario, senha: e.target.value})} placeholder="Senha" required />
                  </div>
                  <div className="space-y-1">
                    <Label>Pontos Iniciais (Par)</Label>
                    <Input type="number" value={novoUsuario.pontos} onChange={e => setNovoUsuario({...novoUsuario, pontos: e.target.value})} placeholder="Ex: 100" required />
                  </div>
                  <div className="space-y-1">
                    <Label>WhatsApp</Label>
                    <Input value={novoUsuario.whatsapp} onChange={e => setNovoUsuario({...novoUsuario, whatsapp: e.target.value})} placeholder="Ex: 11999999999" />
                  </div>
                  <div className="space-y-1">
                    <Label>Tipo de Chave Pix</Label>
                    <Input value={novoUsuario.pix_tipo} onChange={e => setNovoUsuario({...novoUsuario, pix_tipo: e.target.value})} placeholder="Ex: CPF, Telefone, Email" />
                  </div>
                  <div className="space-y-1">
                    <Label>Chave Pix</Label>
                    <Input value={novoUsuario.pix_chave} onChange={e => setNovoUsuario({...novoUsuario, pix_chave: e.target.value})} placeholder="Chave Pix" />
                  </div>
                </div>
                <Button type="submit" className="w-full bg-black text-white hover:bg-gray-800" disabled={loading}>
                  {loading ? 'Cadastrando...' : 'Cadastrar Usuário'}
                </Button>
              </form>
           </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default AdminDashboard
