import { ProgramsCatalog, UniversityCatalog } from '../catalog/CatalogPages';
import { ProgramDetail, UniversityPage } from '../catalog/DetailPages';
import { Unsupported } from '../features/demo/Unsupported';
import { ExamAnalytics, FaqPage, HowItWorks } from '../pages/PublicPages';
import { decodeRouteId } from './navigation';
import { NotFound } from './NotFound';

export function PublicRoute({ path }: { path: string }) {
  if (/^\/universities\/[^/]+$/.test(path)) {
    const id = decodeRouteId(path.slice('/universities/'.length));
    return id ? <UniversityPage key={path} id={id} /> : <NotFound />;
  }
  if (/^\/programs\/[^/]+$/.test(path)) {
    const id = decodeRouteId(path.slice('/programs/'.length));
    return id ? <ProgramDetail key={path} id={id} /> : <NotFound />;
  }
  switch (path) {
    case '/universities': return <UniversityCatalog />;
    case '/programs': return <ProgramsCatalog />;
    case '/ege-analytics': return <Unsupported><ExamAnalytics /></Unsupported>;
    case '/how-it-works': return <HowItWorks />;
    case '/faq': return <FaqPage />;
    default: return <NotFound />;
  }
}
