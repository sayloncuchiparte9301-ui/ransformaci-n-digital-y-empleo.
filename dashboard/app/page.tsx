const indicators = [
  { label: "Empleo total", value: "Pendiente" },
  { label: "Usuarios de internet", value: "Pendiente" },
  { label: "Empleo formal", value: "Pendiente" },
  { label: "Brecha digital", value: "Pendiente" },
];

export default function Page() {
  return (
    <main className="min-h-screen bg-white p-8 text-slate-900">
      <section className="mx-auto max-w-6xl space-y-6">
        <div>
          <h1 className="text-4xl font-bold">Transformación digital y empleo</h1>
          <p className="mt-2 max-w-3xl text-slate-600">
            Dashboard para comparar Ecuador con países de referencia y explicar
            cómo la digitalización influye en el mercado laboral.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-4">
          {indicators.map((item) => (
            <div key={item.label} className="rounded-2xl border p-4 shadow-sm">
              <p className="text-sm text-slate-500">{item.label}</p>
              <p className="text-2xl font-semibold">{item.value}</p>
            </div>
          ))}
        </div>

        <div className="rounded-2xl border p-6 shadow-sm">
          <h2 className="text-xl font-semibold">Interpretación económica</h2>
          <p className="mt-2 text-slate-600">
            Aquí se integrarán gráficos, filtros, tablas y conclusiones.
          </p>
        </div>
      </section>
    </main>
  );
}
