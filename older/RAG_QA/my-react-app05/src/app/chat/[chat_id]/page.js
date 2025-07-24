export default async function Page({ params }) {
  const { chat_id } = await params
  return <div>My Post: {chat_id}</div>
}